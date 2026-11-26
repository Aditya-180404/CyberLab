"""
Purple-Team REST API Router (Phase 9)
Endpoints for atomic attack simulation, purple team campaign runs,
detection efficacy validation, and MITRE coverage gap analysis.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.purple_team import SimulationExecution
from app.core.dependencies import get_current_user, require_role
from app.purple_team.engine import PurpleTeamEngine
from app.schemas.purple_team import (
    SimulationScenarioResponse, ExecuteScenarioRequest, SimulationExecutionResponse,
    ValidationResultResponse, RunCampaignRequest, RunCampaignResponse,
    MitreCoverageResponse, PurpleTeamKPIs
)

router = APIRouter(prefix="/purple-team")


@router.get("/scenarios", response_model=List[SimulationScenarioResponse])
def list_simulation_scenarios(
    tactic: Optional[str] = Query(None, description="Filter scenarios by MITRE tactic"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve available atomic attack simulation scenarios."""
    engine = PurpleTeamEngine(db, current_user.organization_id)
    return engine.get_scenarios(tactic)


@router.post("/execute", response_model=SimulationExecutionResponse)
def execute_atomic_simulation(
    req: ExecuteScenarioRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.SOC_MANAGER, UserRole.SOC_ANALYST]))
):
    """Execute a single atomic attack simulation scenario and validate detection response."""
    try:
        engine = PurpleTeamEngine(db, current_user.organization_id)
        exec_rec = engine.execute_scenario(
            scenario_id=req.scenario_id,
            target_asset_id=req.target_asset_id,
            executed_by=current_user.username,
            parameters=req.parameters
        )

        val_res_dto = None
        if exec_rec.validation_result:
            val_res_dto = ValidationResultResponse(
                id=exec_rec.validation_result.id,
                execution_id=exec_rec.validation_result.execution_id,
                detection_status=exec_rec.validation_result.detection_status,
                matched_alert_id=exec_rec.validation_result.matched_alert_id,
                matched_rule_id=exec_rec.validation_result.matched_rule_id,
                detection_latency_seconds=exec_rec.validation_result.detection_latency_seconds,
                verification_details=exec_rec.validation_result.verification_details,
                created_at=exec_rec.validation_result.created_at
            )

        return SimulationExecutionResponse(
            id=exec_rec.id,
            organization_id=exec_rec.organization_id,
            scenario_id=exec_rec.scenario_id,
            scenario_name=exec_rec.scenario.name if exec_rec.scenario else None,
            mitre_technique_id=exec_rec.scenario.mitre_technique_id if exec_rec.scenario else None,
            mitre_tactic=exec_rec.scenario.mitre_tactic if exec_rec.scenario else None,
            target_asset_id=exec_rec.target_asset_id,
            target_name=exec_rec.target_name,
            executed_by=exec_rec.executed_by,
            status=exec_rec.status,
            executed_at=exec_rec.executed_at,
            completed_at=exec_rec.completed_at,
            execution_log=exec_rec.execution_log,
            validation_result=val_res_dto
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Simulation failed: {str(e)}")


@router.post("/run-campaign", response_model=RunCampaignResponse)
def run_purple_team_campaign(
    req: RunCampaignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.SOC_MANAGER, UserRole.SOC_ANALYST]))
):
    """Execute an automated batch of atomic simulations to measure overall defensive posture."""
    try:
        engine = PurpleTeamEngine(db, current_user.organization_id)
        return engine.run_campaign(
            target_asset_id=req.target_asset_id,
            tactic_filter=req.tactic_filter,
            executed_by=current_user.username
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Campaign failed: {str(e)}")


@router.get("/executions", response_model=List[SimulationExecutionResponse])
def list_simulation_executions(
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List historical simulation runs and verification results."""
    records = db.query(SimulationExecution).filter(
        SimulationExecution.organization_id == current_user.organization_id
    ).order_by(SimulationExecution.executed_at.desc()).limit(limit).all()

    output: List[SimulationExecutionResponse] = []
    for ex in records:
        val_dto = None
        if ex.validation_result:
            val_dto = ValidationResultResponse(
                id=ex.validation_result.id,
                execution_id=ex.validation_result.execution_id,
                detection_status=ex.validation_result.detection_status,
                matched_alert_id=ex.validation_result.matched_alert_id,
                matched_rule_id=ex.validation_result.matched_rule_id,
                detection_latency_seconds=ex.validation_result.detection_latency_seconds,
                verification_details=ex.validation_result.verification_details,
                created_at=ex.validation_result.created_at
            )
        output.append(SimulationExecutionResponse(
            id=ex.id,
            organization_id=ex.organization_id,
            scenario_id=ex.scenario_id,
            scenario_name=ex.scenario.name if ex.scenario else None,
            mitre_technique_id=ex.scenario.mitre_technique_id if ex.scenario else None,
            mitre_tactic=ex.scenario.mitre_tactic if ex.scenario else None,
            target_asset_id=ex.target_asset_id,
            target_name=ex.target_name,
            executed_by=ex.executed_by,
            status=ex.status,
            executed_at=ex.executed_at,
            completed_at=ex.completed_at,
            execution_log=ex.execution_log,
            validation_result=val_dto
        ))
    return output


@router.get("/coverage", response_model=MitreCoverageResponse)
def get_mitre_coverage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve the MITRE ATT&CK defensive detection coverage heatmap and gap analysis."""
    engine = PurpleTeamEngine(db, current_user.organization_id)
    return engine.get_coverage_matrix()


@router.get("/kpis", response_model=PurpleTeamKPIs)
def get_purple_team_kpis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve real-time Purple Team validation KPIs."""
    engine = PurpleTeamEngine(db, current_user.organization_id)
    return engine.get_kpis()
