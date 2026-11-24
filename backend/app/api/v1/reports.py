"""
Enterprise Reports REST API Router (Phase 12)
Endpoints for generating executive posture scorecards and compliance audit reports.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.api.v1.auth import get_current_user
from app.enterprise.report_generator import ReportGenerator
from app.schemas.report import ExecutiveReportResponse, ComplianceReportResponse

router = APIRouter(prefix="/reports")


@router.get("/executive", response_model=ExecutiveReportResponse)
def get_executive_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate executive posture scorecard and strategic recommendations."""
    generator = ReportGenerator(db, current_user.organization_id)
    return generator.generate_executive_report()


@router.get("/compliance", response_model=ComplianceReportResponse)
def get_compliance_report(
    standard: Optional[str] = Query("NIST CSF 2.0 / CIS Controls", description="Target compliance standard"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate technical compliance and audit readiness report."""
    generator = ReportGenerator(db, current_user.organization_id)
    return generator.generate_compliance_report(standard)
