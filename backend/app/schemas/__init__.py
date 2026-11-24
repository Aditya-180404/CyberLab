"""
CyberLab Schemas Package
"""
from app.schemas.auth import LoginRequest, TokenResponse, TokenPayload
from app.schemas.user import UserBase, UserCreate, UserResponse, UserUpdateRole
from app.schemas.health import HealthResponse, PlatformMetrics
from app.schemas.audit import AuditLogResponse
from app.schemas.network import (
    SegmentCreate, SegmentResponse,
    DeviceCreate, DeviceResponse,
    ConnectionCreate, ConnectionResponse,
    TopologyCreate, TopologyUpdate, TopologyResponse, TopologyDetailResponse,
    DeploymentPreview, DeploymentResult
)
from app.schemas.vm import (
    NetworkAdapterInfo, VMRegisterRequest, VMPowerRequest, VMAssociateSegmentRequest,
    VMResponse, VMDiscoveryResult
)

__all__ = [
    "LoginRequest", "TokenResponse", "TokenPayload",
    "UserBase", "UserCreate", "UserResponse", "UserUpdateRole",
    "HealthResponse", "PlatformMetrics",
    "AuditLogResponse",
    "SegmentCreate", "SegmentResponse",
    "DeviceCreate", "DeviceResponse",
    "ConnectionCreate", "ConnectionResponse",
    "TopologyCreate", "TopologyUpdate", "TopologyResponse", "TopologyDetailResponse",
    "DeploymentPreview", "DeploymentResult",
    "NetworkAdapterInfo", "VMRegisterRequest", "VMPowerRequest", "VMAssociateSegmentRequest",
    "VMResponse", "VMDiscoveryResult"
]
