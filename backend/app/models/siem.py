"""
SIEM & Security Telemetry Models (Phase 6)
Stores normalized security events, rule detections, alerts, and correlated incidents.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database.session import Base


class EventCategory:
    AUTHENTICATION = "AUTHENTICATION"
    PROCESS_EXECUTION = "PROCESS_EXECUTION"
    NETWORK_CONNECTION = "NETWORK_CONNECTION"
    FILE_INTEGRITY = "FILE_INTEGRITY"
    SYSTEM_LOG = "SYSTEM_LOG"

    ALL = [AUTHENTICATION, PROCESS_EXECUTION, NETWORK_CONNECTION, FILE_INTEGRITY, SYSTEM_LOG]


class EventSeverity:
    INFORMATIONAL = "INFORMATIONAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    ALL = [INFORMATIONAL, LOW, MEDIUM, HIGH, CRITICAL]


class AlertStatus:
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    CONTAINED = "CONTAINED"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"

    ALL = [OPEN, INVESTIGATING, CONTAINED, RESOLVED, FALSE_POSITIVE]


class IncidentStatus:
    OPEN = "OPEN"
    ACTIVE = "ACTIVE"
    CONTAINED = "CONTAINED"
    CLOSED = "CLOSED"

    ALL = [OPEN, ACTIVE, CONTAINED, CLOSED]


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(String(36), primary_key=True, default=lambda: f"evt-{str(uuid.uuid4())[:8]}")
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Asset context
    asset_id = Column(String(36), ForeignKey("assets.id", ondelete="SET NULL"), nullable=True, index=True)
    hostname = Column(String(100), nullable=True, index=True)
    source_ip = Column(String(45), nullable=True, index=True)
    destination_ip = Column(String(45), nullable=True)

    # Classification
    category = Column(String(50), default=EventCategory.SYSTEM_LOG, nullable=False, index=True)
    severity = Column(String(20), default=EventSeverity.LOW, nullable=False, index=True)
    action = Column(String(30), default="DETECTED", nullable=False)
    message = Column(Text, nullable=False)

    # MITRE ATT&CK Mapping
    mitre_tactic = Column(String(50), nullable=True, index=True)
    mitre_technique_id = Column(String(20), nullable=True, index=True)
    mitre_technique_name = Column(String(100), nullable=True)

    # Payload
    raw_data_json = Column(Text, nullable=True)

    # Relationship
    asset = relationship("Asset")

    __table_args__ = (
        Index("ix_security_events_time_sev", "timestamp", "severity"),
    )


class SecurityAlert(Base):
    __tablename__ = "security_alerts"

    id = Column(String(36), primary_key=True, default=lambda: f"alert-{str(uuid.uuid4())[:8]}")
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    rule_id = Column(String(50), nullable=False, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20), default=EventSeverity.MEDIUM, nullable=False, index=True)
    status = Column(String(20), default=AlertStatus.OPEN, nullable=False, index=True)

    # Affected entity
    asset_id = Column(String(36), ForeignKey("assets.id", ondelete="SET NULL"), nullable=True)
    hostname = Column(String(100), nullable=True, index=True)
    source_ip = Column(String(45), nullable=True)

    # MITRE ATT&CK Tags
    mitre_tactic = Column(String(50), nullable=True)
    mitre_technique_id = Column(String(20), nullable=True)
    mitre_technique_name = Column(String(100), nullable=True)

    # Evidence aggregation
    evidence_count = Column(Integer, default=1, nullable=False)
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Incident correlation
    incident_id = Column(String(36), ForeignKey("security_incidents.id", ondelete="SET NULL"), nullable=True)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    asset = relationship("Asset")
    incident = relationship("SecurityIncident", back_populates="alerts")


class SecurityIncident(Base):
    __tablename__ = "security_incidents"

    id = Column(String(36), primary_key=True, default=lambda: f"inc-{str(uuid.uuid4())[:8]}")
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(150), nullable=False)
    severity = Column(String(20), default=EventSeverity.HIGH, nullable=False, index=True)
    status = Column(String(20), default=IncidentStatus.OPEN, nullable=False, index=True)

    # Scope
    asset_id = Column(String(36), ForeignKey("assets.id", ondelete="SET NULL"), nullable=True)
    primary_hostname = Column(String(100), nullable=True)
    alert_count = Column(Integer, default=1, nullable=False)

    # Threat context
    mitre_tactics_json = Column(Text, nullable=True)  # List of tactics involved
    mitre_techniques_json = Column(Text, nullable=True)  # List of technique IDs
    summary = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    alerts = relationship("SecurityAlert", back_populates="incident")
