"""
Topology Model for Network Studio
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base


class Topology(Base):
    __tablename__ = "topologies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    site_id = Column(String(36), ForeignKey("sites.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(30), default="DRAFT", nullable=False)  # DRAFT, DEPLOYED, STOPPED, FAILED, TEARING_DOWN
    graph_data = Column(Text, nullable=True)  # JSON representation of React Flow nodes and edges
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    segments = relationship("NetworkSegment", back_populates="topology", cascade="all, delete-orphan")
    devices = relationship("NetworkDevice", back_populates="topology", cascade="all, delete-orphan")
    connections = relationship("NetworkConnection", back_populates="topology", cascade="all, delete-orphan")
