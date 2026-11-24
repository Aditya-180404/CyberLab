"""
Purple-Team Schemas (Phase 9)
Pydantic v2 schemas for atomic attack simulations, purple team validation runs,
detection efficacy calculations, and MITRE coverage matrices.
"""
from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class SimulationScenarioResponse(BaseModel):
    id: str
    name: str
    mitre_tactic: str
    mitre_technique_id: str
    mitre_technique_name: str
    description: str
    severity: str
    safe_payload_type: str
    command_template: Optional[str] = None
    expected_detection_rule: Optional[str] = None
    is_atomic: bool = True
    created_at: datetime

    model_config = {"from_attributes": True}


class ExecuteScenarioRequest(BaseModel):
    scenario_id: str
    target_asset_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class ValidationResultResponse(BaseModel):
    id: str
    execution_id: str
    detection_status: str
    matched_alert_id: Optional[str] = None
    matched_rule_id: Optional[str] = None
    detection_latency_seconds: float
    verification_details: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SimulationExecutionResponse(BaseModel):
    id: str
    organization_id: str
    scenario_id: str
    scenario_name: Optional[str] = None
    mitre_technique_id: Optional[str] = None
    mitre_tactic: Optional[str] = None
    target_asset_id: Optional[str] = None
    target_name: Optional[str] = None
    executed_by: str
    status: str
    executed_at: datetime
    completed_at: datetime
    execution_log: Optional[str] = None
    validation_result: Optional[ValidationResultResponse] = None

    model_config = {"from_attributes": True}



class RunCampaignRequest(BaseModel):
    target_asset_id: Optional[str] = None
    tactic_filter: Optional[str] = None


class RunCampaignResponse(BaseModel):
    campaign_id: str
    total_scenarios_executed: int
    detected_count: int
    missed_count: int
    efficacy_rate_pct: float
    executions: List[SimulationExecutionResponse]


class MitreCoverageItem(BaseModel):
    tactic: str
    technique_id: str
    technique_name: str
    total_simulated: int
    detected_count: int
    coverage_status: str = Field(..., description="COVERED, PARTIAL, or GAP")
    detection_efficacy_pct: float
    rule_name: Optional[str] = None


class MitreCoverageResponse(BaseModel):
    total_techniques_tested: int
    covered_techniques: int
    gap_techniques: int
    overall_coverage_pct: float
    coverage_items: List[MitreCoverageItem]


class PurpleTeamKPIs(BaseModel):
    total_simulations: int
    total_detected: int
    total_missed: int
    overall_efficacy_rate: float
    mean_time_to_detect_seconds: float
    by_tactic_efficacy: Dict[str, float]
