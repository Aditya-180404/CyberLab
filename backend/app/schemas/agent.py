"""
Distributed Agent Schemas
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class AgentRegisterRequest(BaseModel):
    hostname: str = Field(..., min_length=2, max_length=100)
    ip_address: str = Field(..., min_length=7, max_length=45)
    os_type: str = "Linux"
    os_release: str = "Linux"
    kernel_version: str = "unknown"
    agent_version: str = "0.4.0"
    hardware_specs: Optional[Dict[str, Any]] = None


class AgentRegisterResponse(BaseModel):
    agent_id: str
    agent_token: str
    heartbeat_interval_sec: int
    policy: Dict[str, Any]


class AgentHeartbeatRequest(BaseModel):
    cpu_pct: float = Field(0.0, ge=0.0, le=100.0)
    memory_pct: float = Field(0.0, ge=0.0, le=100.0)
    disk_pct: float = Field(0.0, ge=0.0, le=100.0)


class AgentHeartbeatResponse(BaseModel):
    status: str
    pending_commands: List[str] = []
    policy_updated: bool = False
    policy: Optional[Dict[str, Any]] = None


class AgentTelemetryBatch(BaseModel):
    cpu_pct: float = 0.0
    memory_pct: float = 0.0
    disk_pct: float = 0.0
    network_connections: Optional[List[Dict[str, Any]]] = []
    processes: Optional[List[Dict[str, Any]]] = []
    auth_events: Optional[List[Dict[str, Any]]] = []
    fim_alerts: Optional[List[Dict[str, Any]]] = []
    installed_packages: Optional[List[Dict[str, str]]] = []


class AgentResponse(BaseModel):
    id: str
    organization_id: str
    hostname: str
    ip_address: str
    os_type: str
    os_release: str
    kernel_version: str
    agent_version: str
    status: str
    last_heartbeat: datetime
    heartbeat_interval_sec: int
    hardware_specs: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentDetailResponse(AgentResponse):
    pending_commands: List[str] = []
    latest_telemetry: Optional[Dict[str, Any]] = None
