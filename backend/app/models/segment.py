"""
Network Segment & Virtual Bridge Model
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base


class NetworkSegment(Base):
    __tablename__ = "network_segments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    topology_id = Column(String(36), ForeignKey("topologies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    bridge_name = Column(String(50), nullable=False)  # e.g. cl-br-dmz
    vlan_id = Column(Integer, nullable=True)
    cidr_block = Column(String(50), nullable=False)  # e.g. 10.10.10.0/24
    gateway_ip = Column(String(45), nullable=True)
    status = Column(String(30), default="INACTIVE", nullable=False)  # ACTIVE, INACTIVE
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    topology = relationship("Topology", back_populates="segments")
    connections = relationship("NetworkConnection", back_populates="segment")
