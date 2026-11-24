"""
Virtual Machine Model for VMware Workstation and Hypervisors
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base


class PowerState:
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    SUSPENDED = "SUSPENDED"
    UNKNOWN = "UNKNOWN"

    ALL = [RUNNING, STOPPED, SUSPENDED, UNKNOWN]


class VirtualMachine(Base):
    __tablename__ = "virtual_machines"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False, index=True)
    hypervisor_type = Column(String(50), default="vmware_workstation", nullable=False)  # vmware_workstation, qemu_kvm
    config_path = Column(String(500), unique=True, nullable=False)  # Absolute path to .vmx
    power_state = Column(String(30), default=PowerState.STOPPED, nullable=False)
    os_type = Column(String(100), default="Linux", nullable=False)
    vcpus = Column(Integer, default=1, nullable=False)
    memory_mb = Column(Integer, default=1024, nullable=False)
    network_adapters_json = Column(Text, nullable=True)  # JSON metadata of ethernet0, ethernet1, etc.
    attached_segment_id = Column(String(36), ForeignKey("network_segments.id", ondelete="SET NULL"), nullable=True)
    is_vulnerable_target = Column(Boolean, default=False, nullable=False)
    safety_warning = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    attached_segment = relationship("NetworkSegment")
