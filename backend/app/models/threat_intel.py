"""
Threat Intelligence (TIP) & Deception / Honeypot Models
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from app.database.session import Base


class ThreatIOC(Base):
    __tablename__ = "threat_iocs"

    id = Column(String(36), primary_key=True, default=lambda: f"ioc-{str(uuid.uuid4())[:8]}")
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    ioc_type = Column(String(20), nullable=False, index=True)  # IP, DOMAIN, SHA256
    value = Column(String(255), nullable=False, index=True)
    threat_actor = Column(String(120), default="Unknown Threat Actor", nullable=False)
    severity = Column(String(20), default="HIGH", nullable=False)
    source = Column(String(80), default="MISP-Community", nullable=False)
    confidence = Column(Integer, default=85, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    hit_count = Column(Integer, default=0, nullable=False)
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class DeceptionTrap(Base):
    __tablename__ = "deception_traps"

    id = Column(String(36), primary_key=True, default=lambda: f"trap-{str(uuid.uuid4())[:8]}")
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    trap_type = Column(String(30), nullable=False)  # CANARY_FILE, DECOY_PORT, DECOY_CREDENTIAL
    target_indicator = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    triggered_count = Column(Integer, default=0, nullable=False)
    last_triggered = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
