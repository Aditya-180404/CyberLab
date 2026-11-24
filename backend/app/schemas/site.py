"""
Site Schemas (Phase 12)
Pydantic v2 models for multi-site enterprise management and telemetry rollups.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SiteCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    location: Optional[str] = Field(default="Primary Datacenter / Lab")
    ip_range: Optional[str] = Field(default=None, description="e.g. 10.10.0.0/16")


class SiteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    ip_range: Optional[str] = None


class SiteResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    description: Optional[str] = None
    location: Optional[str] = None
    status: str
    ip_range: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SiteStatsResponse(BaseModel):
    site_id: str
    name: str
    location: Optional[str] = None
    status: str
    total_assets: int
    active_agents: int
    open_incidents: int
    critical_vulnerabilities: int
    average_risk_score: float
