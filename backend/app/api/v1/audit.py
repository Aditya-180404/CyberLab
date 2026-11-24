"""
Audit Log Query API Router
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogResponse
from app.core.dependencies import require_role

router = APIRouter()


@router.get("/audit", response_model=List[AuditLogResponse])
def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    status_filter: Optional[str] = None,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.AUDITOR, UserRole.SOC_MANAGER])),
    db: Session = Depends(get_db)
):
    """
    Retrieves immutable audit trail records with filtering and pagination.
    Authorized for Super Administrator, Auditor, and SOC Manager roles.
    """
    query = db.query(AuditLog)

    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if status_filter:
        query = query.filter(AuditLog.status == status_filter)

    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    return logs
