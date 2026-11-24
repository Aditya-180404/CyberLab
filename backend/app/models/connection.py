"""
Network Connection (Links & Veth Pairs) Model
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base


class NetworkConnection(Base):
    __tablename__ = "network_connections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    topology_id = Column(String(36), ForeignKey("topologies.id", ondelete="CASCADE"), nullable=False)
    source_device_id = Column(String(36), ForeignKey("network_devices.id", ondelete="CASCADE"), nullable=False)
    target_device_id = Column(String(36), ForeignKey("network_devices.id", ondelete="SET NULL"), nullable=True)
    segment_id = Column(String(36), ForeignKey("network_segments.id", ondelete="SET NULL"), nullable=True)
    veth_name = Column(String(50), nullable=True)  # e.g. cl-ep-srv1
    peer_name = Column(String(50), nullable=True)  # e.g. cl-brp-srv1
    status = Column(String(30), default="DISCONNECTED", nullable=False)  # CONNECTED, DISCONNECTED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    topology = relationship("Topology", back_populates="connections")
    source_device = relationship("NetworkDevice", foreign_keys=[source_device_id], back_populates="out_connections")
    target_device = relationship("NetworkDevice", foreign_keys=[target_device_id])
    segment = relationship("NetworkSegment", back_populates="connections")
