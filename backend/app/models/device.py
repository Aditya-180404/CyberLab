"""
Network Device (Virtual Nodes) Model
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base


class DeviceType:
    ROUTER = "router"
    SWITCH = "switch"
    FIREWALL = "firewall"
    ENDPOINT = "endpoint"
    SERVER = "server"

    ALL = [ROUTER, SWITCH, FIREWALL, ENDPOINT, SERVER]


class NetworkDevice(Base):
    __tablename__ = "network_devices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    topology_id = Column(String(36), ForeignKey("topologies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    device_type = Column(String(30), default=DeviceType.ENDPOINT, nullable=False)
    namespace_name = Column(String(50), nullable=True)  # e.g. cl-ns-web01
    ip_address = Column(String(45), nullable=True)
    mac_address = Column(String(20), nullable=True)
    status = Column(String(30), default="STOPPED", nullable=False)  # STOPPED, RUNNING, ERROR
    config_data = Column(Text, nullable=True)  # JSON for routes, firewall rules, ports
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    topology = relationship("Topology", back_populates="devices")
    out_connections = relationship(
        "NetworkConnection",
        foreign_keys="[NetworkConnection.source_device_id]",
        back_populates="source_device",
        cascade="all, delete-orphan"
    )
