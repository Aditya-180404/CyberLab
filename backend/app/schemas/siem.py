"""
SIEM Schemas & MITRE ATT&CK DTOs (Phase 6)
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class SecurityEventCreate(BaseModel):
    category: str = Field(..., description="AUTHENTICATION, PROCESS_EXECUTION, NETWORK_CONNECTION, FILE_INTEGRITY, SYSTEM_LOG")
    severity: str = Field("LOW", description="INFORMATIONAL, LOW, MEDIUM, HIGH, CRITICAL")
    action: str = Field("DETECTED", description="SUCCESS, FAILURE, DETECTED, BLOCKED")
    message: str = Field(..., min_length=2)
    asset_id: Optional[str] = None
    hostname: Optional[str] = None
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    mitre_tactic: Optional[str] = None
    mitre_technique_id: Optional[str] = None
    mitre_technique_name: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


class SecurityEventResponse(BaseModel):
    id: str
    organization_id: str
    timestamp: datetime
    category: str
    severity: str
    action: str
    message: str
    asset_id: Optional[str] = None
    hostname: Optional[str] = None
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    mitre_tactic: Optional[str] = None
    mitre_technique_id: Optional[str] = None
    mitre_technique_name: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class SecurityAlertResponse(BaseModel):
    id: str
    organization_id: str
    rule_id: str
    title: str
    description: str
    severity: str
    status: str
    asset_id: Optional[str] = None
    hostname: Optional[str] = None
    source_ip: Optional[str] = None
    mitre_tactic: Optional[str] = None
    mitre_technique_id: Optional[str] = None
    mitre_technique_name: Optional[str] = None
    evidence_count: int
    first_seen: datetime
    last_seen: datetime
    incident_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class SecurityIncidentResponse(BaseModel):
    id: str
    organization_id: str
    title: str
    severity: str
    status: str
    asset_id: Optional[str] = None
    primary_hostname: Optional[str] = None
    alert_count: int
    mitre_tactics: List[str] = []
    mitre_techniques: List[str] = []
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MitreTechniqueCount(BaseModel):
    technique_id: str
    technique_name: str
    tactic: str
    event_count: int
    alert_count: int
    last_seen: Optional[datetime] = None


class MitreMatrixSummary(BaseModel):
    total_techniques_mapped: int
    active_techniques_triggered: int
    tactics: Dict[str, List[MitreTechniqueCount]]


class SIEMKPIs(BaseModel):
    total_events: int
    total_alerts: int
    open_alerts: int
    active_incidents: int
    by_severity: Dict[str, int]
    by_category: Dict[str, int]


class AttackSimulationRequest(BaseModel):
    scenario: str = Field(..., description="brute_force, privilege_escalation, credential_dumping, reverse_shell")
    target_hostname: Optional[str] = "metasploitable2"
    target_ip: Optional[str] = "192.168.1.120"
