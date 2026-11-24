"""
Virtual Machine Integration Schemas
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class NetworkAdapterInfo(BaseModel):
    name: str = "ethernet0"
    connection_type: str = "custom"  # custom, hostonly, nat, bridged
    vnet: Optional[str] = "vmnet1"
    mac_address: Optional[str] = None
    virtual_dev: Optional[str] = "e1000"
    is_bridged: bool = False


class VMRegisterRequest(BaseModel):
    config_path: str = Field(..., description="Absolute path to the .vmx configuration file")
    name: Optional[str] = None
    is_vulnerable_target: Optional[bool] = False


class VMDiscoverRequest(BaseModel):
    custom_paths: Optional[List[str]] = None


class VMPowerRequest(BaseModel):
    action: str = Field(..., description="start, stop, reset, or suspend")
    mode: str = Field(default="soft", description="soft or hard")


class VMAssociateSegmentRequest(BaseModel):
    segment_id: Optional[str] = None


class VMResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    hypervisor_type: str
    config_path: str
    power_state: str
    os_type: str
    vcpus: int
    memory_mb: int
    network_adapters: List[NetworkAdapterInfo] = []
    attached_segment_id: Optional[str] = None
    is_vulnerable_target: bool
    safety_warning: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VMDiscoveryResult(BaseModel):
    discovered_count: int
    registered_vms: List[VMResponse]
    scanned_paths: List[str]
