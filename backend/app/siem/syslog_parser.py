"""
Syslog, OPNsense Firewall, Suricata EVE & Zeek NDR Parsers
Converts raw network appliance and endpoint log lines into normalized SecurityEventCreate payloads.
"""
import json
import re
from typing import Optional, Dict, Any
from app.models.siem import EventCategory, EventSeverity
from app.schemas.siem import SecurityEventCreate

_IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_SSH_FAIL_RE = re.compile(r"(?:Failed password|Invalid user|authentication failure).*?from\s+((?:\d{1,3}\.){3}\d{1,3})", re.IGNORECASE)
_SUDO_RE = re.compile(r"sudo:\s+.*?(?:NOT in sudoers|authentication failure|COMMAND=.*)", re.IGNORECASE)


def parse_syslog_line(raw_line: str, source_name: str = "syslog", fallback_ip: Optional[str] = None) -> SecurityEventCreate:
    """Parses RFC3164/5424 syslog lines, OPNsense filterlog, Suricata JSON, and Linux auth logs."""
    line = raw_line.strip()

    # 1. Embedded Suricata EVE JSON inside syslog
    json_idx = line.find("{")
    if json_idx != -1 and '"event_type"' in line[json_idx:]:
        try:
            eve = json.loads(line[json_idx:])
            return parse_ndr_event("suricata", eve, source_name)
        except Exception:
            pass

    # 2. OPNsense / pfSense filterlog
    if "filterlog" in line.lower():
        ips = _IP_RE.findall(line)
        src_ip = ips[0] if len(ips) >= 1 else fallback_ip
        dst_ip = ips[1] if len(ips) >= 2 else None
        is_block = ",block," in line.lower() or " block " in line.lower()
        return SecurityEventCreate(
            category=EventCategory.NETWORK_CONNECTION,
            severity=EventSeverity.MEDIUM if is_block else EventSeverity.LOW,
            action="BLOCK" if is_block else "PASS",
            message=f"[{source_name}] Firewall {'blocked' if is_block else 'logged'} packet from {src_ip or 'unknown'} to {dst_ip or 'unknown'}: {line[:180]}",
            hostname=source_name,
            source_ip=src_ip,
            destination_ip=dst_ip,
            mitre_tactic="Discovery" if is_block else None,
            mitre_technique_id="T1046" if is_block else None,
            raw_data={"syslog_source": source_name, "raw": line},
        )

    # 3. SSH Auth Failures
    m_ssh = _SSH_FAIL_RE.search(line)
    if m_ssh:
        attacker_ip = m_ssh.group(1)
        return SecurityEventCreate(
            category=EventCategory.AUTHENTICATION,
            severity=EventSeverity.MEDIUM,
            action="FAILURE",
            message=line,
            hostname=source_name,
            source_ip=attacker_ip,
            mitre_tactic="Credential Access",
            mitre_technique_id="T1110",
            raw_data={"syslog_source": source_name, "raw": line},
        )

    # 4. Sudo / Privilege Escalation
    if _SUDO_RE.search(line):
        is_abuse = "not in sudoers" in line.lower() or "authentication failure" in line.lower()
        return SecurityEventCreate(
            category=EventCategory.AUTHENTICATION,
            severity=EventSeverity.HIGH if is_abuse else EventSeverity.LOW,
            action="FAILURE" if is_abuse else "EXECUTED",
            message=line,
            hostname=source_name,
            source_ip=fallback_ip,
            mitre_tactic="Privilege Escalation",
            mitre_technique_id="T1548.003",
            raw_data={"syslog_source": source_name, "raw": line},
        )

    # 5. Generic Syslog Normalization
    ips = _IP_RE.findall(line)
    return SecurityEventCreate(
        category=EventCategory.SYSTEM_LOG,
        severity=EventSeverity.LOW,
        action="LOG",
        message=line,
        hostname=source_name,
        source_ip=ips[0] if ips else fallback_ip,
        destination_ip=ips[1] if len(ips) > 1 else None,
        raw_data={"syslog_source": source_name, "raw": line},
    )


def parse_ndr_event(engine: str, payload: Dict[str, Any], sensor_name: str = "ndr-sensor") -> SecurityEventCreate:
    """Normalizes Suricata EVE JSON or Zeek network metadata events into CyberLab SIEM format."""
    src_ip = payload.get("src_ip") or payload.get("id.orig_h")
    dst_ip = payload.get("dest_ip") or payload.get("id.resp_h")
    dst_port = payload.get("dest_port") or payload.get("id.resp_p")

    if engine == "suricata":
        alert = payload.get("alert") or {}
        sig = alert.get("signature") or payload.get("event_type", "Suricata Network Flow")
        sev_num = alert.get("severity", 3)
        sev = EventSeverity.CRITICAL if sev_num == 1 else EventSeverity.HIGH if sev_num == 2 else EventSeverity.MEDIUM if alert else EventSeverity.LOW
        is_alert = bool(alert)
        return SecurityEventCreate(
            category=EventCategory.NETWORK_CONNECTION,
            severity=sev,
            action="NDR_ALERT" if is_alert else "FLOW",
            message=f"[Suricata] {sig} ({src_ip or '?'} -> {dst_ip or '?'}:{dst_port or '?'})",
            hostname=payload.get("host") or sensor_name,
            source_ip=src_ip,
            destination_ip=dst_ip,
            mitre_tactic="Discovery" if "scan" in sig.lower() else "Command and Control" if is_alert else None,
            mitre_technique_id="T1046" if "scan" in sig.lower() else "T1071" if is_alert else None,
            raw_data={"ndr_engine": "suricata", "suricata_alert": is_alert, **payload},
        )

    # Zeek or generic firewall flow
    proto = payload.get("proto", "tcp")
    service = payload.get("service", "")
    query = payload.get("query") or payload.get("host") or ""
    msg = f"[{engine.upper()}] {proto.upper()} {service} {src_ip or '?'} -> {dst_ip or '?'}:{dst_port or '?'}"
    if query:
        msg += f" ({query})"

    return SecurityEventCreate(
        category=EventCategory.NETWORK_CONNECTION,
        severity=EventSeverity.LOW,
        action="FLOW",
        message=msg,
        hostname=sensor_name,
        source_ip=src_ip,
        destination_ip=dst_ip,
        raw_data={"ndr_engine": engine, **payload},
    )
