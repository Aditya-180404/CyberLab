"""
SOAR API Router (Phase 7)
Provides containment playbook management, approval gates, action execution, and rollback.
"""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.soar import SOARPlaybook, SOARAction, ActionStatus
from app.models.audit import AuditLog
from app.schemas.soar import (
    SOARPlaybookResponse, SOARActionCreateRequest, SOARActionResponse,
    SOARApprovalDecisionRequest, SOARKPIs
)
from app.soar.engine import soar_engine
from app.core.dependencies import get_current_user, require_role

router = APIRouter()


def _format_action(a: SOARAction) -> SOARActionResponse:
    return SOARActionResponse(
        id=a.id,
        organization_id=a.organization_id,
        playbook_id=a.playbook_id,
        action_type=a.action_type,
        status=a.status,
        target_type=a.target_type,
        target_id=a.target_id,
        target_name=a.target_name,
        incident_id=a.incident_id,
        requested_by=a.requested_by,
        approved_by=a.approved_by,
        rejection_reason=a.rejection_reason,
        executed_at=a.executed_at,
        verified=a.verified,
        verification_details=a.verification_details,
        rollback_supported=a.rollback_supported,
        is_rolled_back=a.is_rolled_back,
        rollback_details=a.rollback_details,
        parameters=json.loads(a.parameters_json or "{}") if a.parameters_json else None,
        output_log=a.output_log,
        created_at=a.created_at,
        updated_at=a.updated_at
    )


@router.get("/soar/playbooks", response_model=List[SOARPlaybookResponse])
def list_playbooks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists available automated containment playbooks, ensuring baseline playbooks are seeded."""
    soar_engine.ensure_default_playbooks(db)
    playbooks = db.query(SOARPlaybook).filter(SOARPlaybook.is_enabled == True).all()
    return [SOARPlaybookResponse.model_validate(p) for p in playbooks]


@router.post("/soar/playbooks/{playbook_id}/execute", response_model=SOARActionResponse)
def execute_playbook(
    playbook_id: str,
    payload: SOARActionCreateRequest,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.SOC_MANAGER, UserRole.SOC_ANALYST])),
    db: Session = Depends(get_db)
):
    """Triggers playbook execution against a target entity, passing through human approval if required."""
    soar_engine.ensure_default_playbooks(db)
    pb = db.query(SOARPlaybook).filter(SOARPlaybook.id == playbook_id).first()
    if not pb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Playbook '{playbook_id}' not found")

    auto_approve = not pb.requires_approval

    action = soar_engine.create_action(
        db,
        action_type=pb.action_type,
        target_id=payload.target_id,
        target_name=payload.target_name,
        target_type=payload.target_type,
        playbook_id=pb.id,
        incident_id=payload.incident_id,
        requested_by=current_user.username,
        parameters=payload.parameters,
        auto_approve=auto_approve
    )

    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="SOAR_PLAYBOOK_TRIGGERED",
        resource_type="soar_action",
        resource_id=action.id,
        status="SUCCESS",
        details=f"User '{current_user.username}' triggered playbook '{pb.name}' on {payload.target_id} (Status: {action.status})"
    )
    db.add(audit)
    db.commit()

    return _format_action(action)


@router.get("/soar/actions", response_model=List[SOARActionResponse])
def list_actions(
    status_filter: Optional[str] = Query(None, alias="status"),
    action_type: Optional[str] = Query(None),
    incident_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists history of SOAR containment actions with live execution and verification status."""
    query = db.query(SOARAction)
    if status_filter:
        query = query.filter(SOARAction.status == status_filter)
    if action_type:
        query = query.filter(SOARAction.action_type == action_type)
    if incident_id:
        query = query.filter(SOARAction.incident_id == incident_id)

    actions = query.order_by(SOARAction.created_at.desc()).all()
    return [_format_action(a) for a in actions]


@router.post("/soar/actions/{action_id}/approve", response_model=SOARActionResponse)
def approve_action(
    action_id: str,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.SOC_MANAGER, UserRole.SOC_ANALYST])),
    db: Session = Depends(get_db)
):
    """Human-in-the-loop authorization gate: Approves and immediately dispatches the containment action."""
    action = db.query(SOARAction).filter(SOARAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found")

    if action.status != ActionStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot approve action in status '{action.status}'")

    action = soar_engine.execute_action(db, action, approved_by=current_user.username)

    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="SOAR_ACTION_APPROVED",
        resource_type="soar_action",
        resource_id=action.id,
        status="SUCCESS",
        details=f"Analyst '{current_user.username}' approved SOAR action '{action.action_type}' for target '{action.target_name}'"
    )
    db.add(audit)
    db.commit()

    return _format_action(action)


@router.post("/soar/actions/{action_id}/reject", response_model=SOARActionResponse)
def reject_action(
    action_id: str,
    payload: SOARApprovalDecisionRequest,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.SOC_MANAGER, UserRole.SOC_ANALYST])),
    db: Session = Depends(get_db)
):
    """Rejects a pending response action."""
    action = db.query(SOARAction).filter(SOARAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found")

    if action.status != ActionStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot reject action in status '{action.status}'")

    action.status = ActionStatus.REJECTED
    action.approved_by = current_user.username
    action.rejection_reason = payload.reason or "Rejected by security analyst."
    db.commit()

    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="SOAR_ACTION_REJECTED",
        resource_type="soar_action",
        resource_id=action.id,
        status="SUCCESS",
        details=f"Analyst '{current_user.username}' rejected action: {action.rejection_reason}"
    )
    db.add(audit)
    db.commit()

    return _format_action(action)


@router.post("/soar/actions/{action_id}/rollback", response_model=SOARActionResponse)
def rollback_action(
    action_id: str,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.SOC_MANAGER, UserRole.SOC_ANALYST])),
    db: Session = Depends(get_db)
):
    """Executes state rollback, safely reversing the containment operation."""
    try:
        action = soar_engine.rollback_action(db, action_id, current_user.username)
        return _format_action(action)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/soar/kpis", response_model=SOARKPIs)
def get_soar_kpis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns aggregated SOAR execution metrics and approval queue count."""
    data = soar_engine.get_kpis(db)
    return SOARKPIs(**data)
