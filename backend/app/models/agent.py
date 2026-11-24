"""
Distributed Linux Agent & Telemetry Models
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base


class AgentStatus:
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    ISOLATED = "ISOLATED"
    REVOKED = "REVOKED"

    ALL = [ONLINE, OFFLINE, ISOLATED, REVOKED]


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True, default=lambda: f"cl-agent-{str(uuid.uuid4())[:8]}")
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    site_id = Column(String(36), ForeignKey("sites.id", ondelete="SET NULL"), nullable=True)
    hostname = Column(String(100), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)
    os_type = Column(String(50), default="Linux", nullable=False)
    os_release = Column(String(100), default="Linux", nullable=False)
    kernel_version = Column(String(100), default="unknown", nullable=False)
    agent_version = Column(String(20), default="0.4.0", nullable=False)
    status = Column(String(20), default=AgentStatus.ONLINE, nullable=False)
    agent_token_hash = Column(String(255), nullable=False)
    last_heartbeat = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    heartbeat_interval_sec = Column(Integer, default=10, nullable=False)
    hardware_specs_json = Column(Text, nullable=True)  # CPU cores, total RAM, disk
    policy_json = Column(Text, nullable=True)  # Monitored FIM paths, rules
    pending_commands_json = Column(Text, nullable=True)  # Action queue (e.g. ["ISOLATE"])
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    telemetry = relationship("AgentTelemetry", back_populates="agent", cascade="all, delete-orphan", order_by="desc(AgentTelemetry.created_at)")


class AgentTelemetry(Base):
    __tablename__ = "agent_telemetry"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    cpu_pct = Column(Float, default=0.0, nullable=False)
    memory_pct = Column(Float, default=0.0, nullable=False)
    disk_pct = Column(Float, default=0.0, nullable=False)
    network_connections_json = Column(Text, nullable=True)  # Listening ports, remote connections
    processes_json = Column(Text, nullable=True)  # Process snapshot
    auth_events_json = Column(Text, nullable=True)  # SSH, sudo, logins
    fim_alerts_json = Column(Text, nullable=True)  # File changes
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    agent = relationship("Agent", back_populates="telemetry")
