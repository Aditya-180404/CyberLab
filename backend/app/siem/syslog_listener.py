"""
Lightweight Non-Privileged UDP Syslog Receiver (Port 5514 by default)
Allows firewalls (OPNsense/pfSense), Suricata, and Linux rsyslog forwarders to stream logs directly.
"""
import asyncio
import logging
from typing import Optional
from app.database.session import SessionLocal
from app.siem.syslog_parser import parse_syslog_line
from app.siem.engine import siem_engine
from app.models.organization import Organization

logger = logging.getLogger("cyberlab.syslog")


class _SyslogUDPProtocol(asyncio.DatagramProtocol):
    def datagram_received(self, data: bytes, addr):
        text = data.decode("utf-8", errors="ignore").strip()
        if not text:
            return
        src_ip = addr[0] if addr else None
        db = SessionLocal()
        try:
            org = db.query(Organization).first()
            org_id = org.id if org else "default-org"
            for line in text.splitlines():
                if not line.strip():
                    continue
                evt = parse_syslog_line(line, source_name=src_ip or "syslog-udp", fallback_ip=src_ip)
                siem_engine.ingest_event(db, evt, organization_id=org_id)
        except Exception as e:
            logger.error(f"Failed processing UDP syslog from {src_ip}: {e}")
        finally:
            db.close()


async def start_syslog_listener(port: int = 5514) -> Optional[asyncio.DatagramTransport]:
    try:
        loop = asyncio.get_running_loop()
        transport, _ = await loop.create_datagram_endpoint(
            _SyslogUDPProtocol,
            local_addr=("0.0.0.0", port),
        )
        logger.info(f"UDP Syslog/NDR collector listening on 0.0.0.0:{port}")
        return transport
    except Exception as e:
        logger.warning(f"Could not bind UDP Syslog listener on port {port}: {e}")
        return None
