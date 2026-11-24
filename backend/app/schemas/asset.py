"""
Unified Asset Inventory Schemas (Phase 5)
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class AssetResponse(BaseModel):
    id: str
    organization_id: str
    site_id: Optional[str] = None
    name: str
    asset_type: str
    ip_addresses: List[str] = []
    mac_addresses: List[str] = []
    os_family: str
    os_version: str
    kernel_version: Optional[str] = None
    criticality: str
    risk_score: int
    exposure: str
    status: str
    virtual_machine_id: Optional[str] = None
    agent_id: Optional[str] = None
    network_device_id: Optional[str] = None
    hardware_specs: Optional[Dict[str, Any]] = None
    services: Optional[List[Dict[str, Any]]] = None
    software_inventory: Optional[List[Dict[str, Any]]] = None
    security_tags: List[str] = []
    last_seen: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssetDetailResponse(AssetResponse):
    vm_details: Optional[Dict[str, Any]] = None
    agent_details: Optional[Dict[str, Any]] = None
    device_details: Optional[Dict[str, Any]] = None


class AssetCriticalityUpdateRequest(BaseModel):
    criticality: str = Field(..., pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    exposure: Optional[str] = Field(None, pattern="^(INTERNAL|ISOLATED|DMZ|PUBLIC)$")


class AssetSyncResult(BaseModel):
    total_synced: int
    vm_assets_synced: int
    agent_assets_synced: int
    simulated_assets_synced: int
    message: str


class AssetInventoryKPIs(BaseModel):
    total_assets: int
    average_risk_score: float
    high_risk_count: int
    critical_assets_count: int
    by_type: Dict[str, int]
    by_criticality: Dict[str, int]
