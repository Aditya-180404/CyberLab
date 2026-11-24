"""
Security & Compliance Reporting Schemas (Phase 12)
Pydantic v2 schemas for executive summaries, posture scorecards, and compliance audits.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class TopRiskItem(BaseModel):
    category: str
    item_name: str
    severity: str
    impact: str
    recommended_action: str


class ExecutiveReportResponse(BaseModel):
    report_id: str
    title: str
    organization_name: str
    generated_at: datetime
    overall_posture_score: int  # 0 to 100 (100 = completely secure)
    posture_level: str  # EXCELLENT, ACCEPTABLE, AT_RISK, CRITICAL
    executive_summary: str
    kpi_summary: Dict[str, Any]
    top_risks: List[TopRiskItem]
    remediation_recommendations: List[str]
    report_markdown: str


class ComplianceControlItem(BaseModel):
    control_id: str
    family: str
    title: str
    status: str  # COMPLIANT, PARTIAL, NON_COMPLIANT
    coverage_score_pct: float
    evidence: str


class ComplianceReportResponse(BaseModel):
    report_id: str
    title: str
    organization_name: str
    standard: str
    generated_at: datetime
    compliance_score_pct: float
    certification_status: str  # AUDIT_READY, CONDITIONALLY_COMPLIANT, NON_COMPLIANT
    summary: str
    controls: List[ComplianceControlItem]
    evidence_count: int
    report_markdown: str
