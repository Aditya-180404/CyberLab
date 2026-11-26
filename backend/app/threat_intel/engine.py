"""
Threat Intelligence & Deception Engine
Correlates network traffic, endpoint sockets, and logs against IOCs and decoy traps.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.threat_intel import ThreatIOC, DeceptionTrap

DEFAULT_IOCS = [
    {
        "ioc_type": "IP",
        "value": "198.51.100.50",
        "threat_actor": "APT-Lab-Simulator",
        "severity": "CRITICAL",
        "source": "MISP-ThreatFeed",
        "confidence": 95,
    },
    {
        "ioc_type": "IP",
        "value": "203.0.113.66",
        "threat_actor": "Mirai-Scanner-Botnet",
        "severity": "HIGH",
        "source": "AbuseIPDB-Sync",
        "confidence": 90,
    },
    {
        "ioc_type": "IP",
        "value": "45.155.205.233",
        "threat_actor": "BruteForce-SSH-C2",
        "severity": "HIGH",
        "source": "AlienVault-OTX",
        "confidence": 88,
    },
    {
        "ioc_type": "DOMAIN",
        "value": "c2.evil-beacon.test",
        "threat_actor": "Sliver-C2-Lab",
        "severity": "CRITICAL",
        "source": "OpenCTI-Graph",
        "confidence": 98,
    },
    {
        "ioc_type": "SHA256",
        "value": "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f",
        "threat_actor": "EICAR-Test-Signature",
        "severity": "HIGH",
        "source": "ClamAV-YARA",
        "confidence": 100,
    },
]

DEFAULT_TRAPS = [
    {
        "name": "SSH Root Canary Key",
        "trap_type": "CANARY_FILE",
        "target_indicator": "/etc/cyberlab_canary.key",
        "description": "Decoy private SSH key monitored via agent FIM; any access triggers critical alert.",
    },
    {
        "name": "Decoy Telnet Honeypot (Port 2323)",
        "trap_type": "DECOY_PORT",
        "target_indicator": "port:2323",
        "description": "Internal deception listener trapping lateral port sweeps and credential probes.",
    },
    {
        "name": "Honey Admin Account",
        "trap_type": "DECOY_CREDENTIAL",
        "target_indicator": "svc-backup-admin",
        "description": "Unused decoy username; any authentication attempt indicates active reconnaissance.",
    },
]


class ThreatIntelEngine:
    def __init__(self, db: Session, organization_id: str):
        self.db = db
        self.organization_id = organization_id
        self.ensure_defaults()

    def ensure_defaults(self) -> None:
        if self.db.query(ThreatIOC).filter(ThreatIOC.organization_id == self.organization_id).count() == 0:
            for item in DEFAULT_IOCS:
                self.db.add(ThreatIOC(id=f"ioc-{str(uuid.uuid4())[:8]}", organization_id=self.organization_id, **item))
        if self.db.query(DeceptionTrap).filter(DeceptionTrap.organization_id == self.organization_id).count() == 0:
            for trap in DEFAULT_TRAPS:
                self.db.add(DeceptionTrap(id=f"trap-{str(uuid.uuid4())[:8]}", organization_id=self.organization_id, **trap))
        self.db.commit()

    def list_iocs(self) -> List[ThreatIOC]:
        return self.db.query(ThreatIOC).filter(
            ThreatIOC.organization_id == self.organization_id
        ).order_by(ThreatIOC.created_at.desc()).all()

    def add_ioc(self, payload) -> ThreatIOC:
        ioc = ThreatIOC(
            id=f"ioc-{str(uuid.uuid4())[:8]}",
            organization_id=self.organization_id,
            ioc_type=payload.ioc_type,
            value=payload.value.strip().lower() if payload.ioc_type != "IP" else payload.value.strip(),
            threat_actor=payload.threat_actor,
            severity=payload.severity,
            source=payload.source,
            confidence=payload.confidence,
        )
        self.db.add(ioc)
        self.db.commit()
        self.db.refresh(ioc)
        return ioc

    def delete_ioc(self, ioc_id: str) -> None:
        ioc = self.db.query(ThreatIOC).filter(
            ThreatIOC.id == ioc_id, ThreatIOC.organization_id == self.organization_id
        ).first()
        if not ioc:
            raise ValueError(f"IOC '{ioc_id}' not found")
        self.db.delete(ioc)
        self.db.commit()

    def match_indicators(self, candidates: List[str]) -> List[ThreatIOC]:
        """Checks a list of IP/domain/hash strings against active Threat IOCs."""
        clean = {c.strip().lower() for c in candidates if c and c.strip()}
        if not clean:
            return []
        active_iocs = self.db.query(ThreatIOC).filter(
            ThreatIOC.organization_id == self.organization_id,
            ThreatIOC.is_active == True,  # noqa: E712
        ).all()

        matched: List[ThreatIOC] = []
        now = datetime.now(timezone.utc)
        for ioc in active_iocs:
            val_lower = ioc.value.lower()
            if val_lower in clean or any(val_lower in cand for cand in clean):
                ioc.hit_count += 1
                ioc.last_seen = now
                matched.append(ioc)
        if matched:
            self.db.flush()
        return matched

    def list_traps(self) -> List[DeceptionTrap]:
        return self.db.query(DeceptionTrap).filter(
            DeceptionTrap.organization_id == self.organization_id
        ).order_by(DeceptionTrap.created_at.desc()).all()

    def add_trap(self, payload) -> DeceptionTrap:
        trap = DeceptionTrap(
            id=f"trap-{str(uuid.uuid4())[:8]}",
            organization_id=self.organization_id,
            name=payload.name,
            trap_type=payload.trap_type,
            target_indicator=payload.target_indicator,
            description=payload.description,
        )
        self.db.add(trap)
        self.db.commit()
        self.db.refresh(trap)
        return trap

    def mark_trap_triggered(self, trap: DeceptionTrap) -> DeceptionTrap:
        trap.triggered_count += 1
        trap.last_triggered = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(trap)
        return trap
