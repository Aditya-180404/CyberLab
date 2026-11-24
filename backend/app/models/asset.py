"""
Unified Asset Inventory Model (Phase 5)
Aggregates and normalizes assets across Simulated Devices, Virtual Machines, and Distributed Agents.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base


class AssetType:
    VIRTUAL_MACHINE = "VIRTUAL_MACHINE"
    AGENT_HOST = "AGENT_HOST"
    SIMULATED_DEVICE = "SIMULATED_DEVICE"
    PHYSICAL_HOST = "PHYSICAL_HOST"

    ALL = [VIRTUAL_MACHINE, AGENT_HOST, SIMULATED_DEVICE, PHYSICAL_HOST]


class AssetCriticality:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    ALL = [LOW, MEDIUM, HIGH, CRITICAL]


class AssetStatus:
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    QUARANTINED = "QUARANTINED"
    DECOMMISSIONED = "DECOMMISSIONED"

    ALL = [ACTIVE, INACTIVE, QUARANTINED, DECOMMISSIONED]


class Asset(Base):
    __tablename__ = "assets"

    id = Column(String(36), primary_key=True, default=lambda: f"asset-{str(uuid.uuid4())[:8]}")
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    site_id = Column(String(36), ForeignKey("sites.id", ondelete="SET NULL"), nullable=True)

    # Identifiers
    name = Column(String(100), nullable=False, index=True)
    asset_type = Column(String(30), default=AssetType.VIRTUAL_MACHINE, nullable=False, index=True)
    ip_addresses_json = Column(Text, nullable=True)  # List of IPv4 / IPv6 strings
    mac_addresses_json = Column(Text, nullable=True)  # List of MAC address strings

    # System Fingerprint
    os_family = Column(String(50), default="Linux", nullable=False)  # Linux, Windows, BSD, NetworkOS
    os_version = Column(String(100), default="Unknown", nullable=False)
    kernel_version = Column(String(100), nullable=True)

    # Security & Risk Posture
    criticality = Column(String(20), default=AssetCriticality.MEDIUM, nullable=False)
    risk_score = Column(Integer, default=0, nullable=False)  # 0 to 100
    exposure = Column(String(20), default="INTERNAL", nullable=False)  # INTERNAL, ISOLATED, DMZ, PUBLIC
    status = Column(String(20), default=AssetStatus.ACTIVE, nullable=False)

    # Source Linkages
    virtual_machine_id = Column(String(36), ForeignKey("virtual_machines.id", ondelete="SET NULL"), nullable=True)
    agent_id = Column(String(36), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    network_device_id = Column(String(36), ForeignKey("network_devices.id", ondelete="SET NULL"), nullable=True)

    # Deep Telemetry & Inventory
    hardware_specs_json = Column(Text, nullable=True)  # vCPUs, RAM MB, Storage GB
    services_json = Column(Text, nullable=True)  # Discovered open listening ports & services
    software_inventory_json = Column(Text, nullable=True)  # Installed packages / components
    security_tags_json = Column(Text, nullable=True)  # ["VULNERABLE_TARGET", "FIM_ALERT", "SSH_EXPOSED"]

    # Timestamps
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    virtual_machine = relationship("VirtualMachine")
    agent = relationship("Agent")
    network_device = relationship("NetworkDevice")
