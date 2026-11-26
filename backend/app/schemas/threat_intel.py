"""
Threat Intelligence & Deception Pydantic Schemas
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ThreatIOCCreate(BaseModel):
    ioc_type: str = Field(..., pattern="^(IP|DOMAIN|SHA256)$")
    value: str = Field(..., min_length=3, max_length=255)
    threat_actor: str = Field(default="External Adversary", max_length=120)
    severity: str = Field(default="HIGH", pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    source: str = Field(default="MISP-Feed", max_length=80)
    confidence: int = Field(default=85, ge=0, le=100)


class ThreatIOCResponse(BaseModel):
    id: str
    organization_id: str
    ioc_type: str
    value: str
    threat_actor: str
    severity: str
    source: str
    confidence: int
    is_active: bool
    hit_count: int
    last_seen: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DeceptionTrapCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    trap_type: str = Field(..., pattern="^(CANARY_FILE|DECOY_PORT|DECOY_CREDENTIAL)$")
    target_indicator: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None


class DeceptionTrapResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    trap_type: str
    target_indicator: str
    description: Optional[str] = None
    is_active: bool
    triggered_count: int
    last_triggered: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SyslogBatchRequest(BaseModel):
    source_name: str = Field(default="opnsense-fw", max_length=100)
    source_ip: Optional[str] = None
    lines: List[str] = Field(..., min_length=1, max_length=200)


class NDRIngestRequest(BaseModel):
    engine: str = Field(default="suricata", pattern="^(suricata|zeek|firewall)$")
    events: List[Dict[str, Any]] = Field(..., min_length=1, max_length=200)
