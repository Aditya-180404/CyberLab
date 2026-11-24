"""
Network Simulation Schemas
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class SegmentBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    bridge_name: str = Field(..., min_length=3, max_length=50)
    vlan_id: Optional[int] = Field(None, ge=1, le=4094)
    cidr_block: str = Field(..., description="e.g. 10.10.10.0/24")
    gateway_ip: Optional[str] = None


class SegmentCreate(SegmentBase):
    pass


class SegmentResponse(SegmentBase):
    id: str
    topology_id: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeviceBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    device_type: str = Field(default="endpoint")
    namespace_name: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    config_data: Optional[str] = None


class DeviceCreate(DeviceBase):
    pass


class DeviceResponse(DeviceBase):
    id: str
    topology_id: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConnectionBase(BaseModel):
    source_device_id: str
    target_device_id: Optional[str] = None
    segment_id: Optional[str] = None
    veth_name: Optional[str] = None
    peer_name: Optional[str] = None


class ConnectionCreate(ConnectionBase):
    pass


class ConnectionResponse(ConnectionBase):
    id: str
    topology_id: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TopologyBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    site_id: Optional[str] = None
    graph_data: Optional[str] = None


class TopologyCreate(TopologyBase):
    segments: Optional[List[SegmentCreate]] = []
    devices: Optional[List[DeviceCreate]] = []
    connections: Optional[List[ConnectionCreate]] = []


class TopologyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    graph_data: Optional[str] = None


class TopologyResponse(TopologyBase):
    id: str
    organization_id: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TopologyDetailResponse(TopologyResponse):
    segments: List[SegmentResponse] = []
    devices: List[DeviceResponse] = []
    connections: List[ConnectionResponse] = []


class DeploymentPreview(BaseModel):
    topology_id: str
    topology_name: str
    namespaces_to_create: List[str]
    bridges_to_create: List[str]
    veth_pairs_to_create: List[Dict[str, str]]
    nftables_tables_to_create: List[str]
    safety_check_passed: bool
    protected_interfaces_safe: bool
    estimated_memory_kb: int


class DeploymentResult(BaseModel):
    topology_id: str
    status: str
    details: Dict[str, Any]
    message: str
