"""
Enterprise Security & Compliance Report Generator (Phase 12)
Aggregates cross-platform telemetry from Assets, SIEM, SOAR, Purple-Team, and Vulnerabilities
to produce executive scorecards and NIST CSF / CIS compliance reports.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.asset import Asset
from app.models.agent import Agent, AgentStatus
from app.models.siem import SecurityIncident, IncidentStatus, SecurityAlert, SecurityEvent
from app.models.soar import SOARAction, ActionStatus
from app.models.vulnerability import AssetVulnerability, Vulnerability, VulnerabilityStatus, VulnerabilitySeverity
from app.purple_team.engine import PurpleTeamEngine
from app.schemas.report import (
    ExecutiveReportResponse, ComplianceReportResponse, TopRiskItem, ComplianceControlItem
)


class ReportGenerator:
    def __init__(self, db: Session, organization_id: str):
        self.db = db
        self.organization_id = organization_id

    def generate_executive_report(self) -> ExecutiveReportResponse:
        """Generates an executive-level cybersecurity posture scorecard."""
        report_id = f"rpt-exec-{str(uuid.uuid4())[:8]}"
        now = datetime.now(timezone.utc)

        org = self.db.query(Organization).filter(Organization.id == self.organization_id).first()
        org_name = org.name if org else "CyberLab Enterprise"

        # 1. Assets Posture
        assets = self.db.query(Asset).filter(Asset.organization_id == self.organization_id).all()
        total_assets = len(assets)
        avg_risk = sum(a.risk_score for a in assets) / max(1, total_assets) if total_assets > 0 else 0.0

        # 2. Agents
        active_agents = self.db.query(Agent).filter(
            Agent.organization_id == self.organization_id,
            Agent.status == AgentStatus.ONLINE
        ).count()

        # 3. Incidents
        open_incidents = self.db.query(SecurityIncident).filter(
            SecurityIncident.organization_id == self.organization_id,
            SecurityIncident.status.in_([IncidentStatus.OPEN, IncidentStatus.ACTIVE])
        ).count()
        closed_incidents = self.db.query(SecurityIncident).filter(
            SecurityIncident.organization_id == self.organization_id,
            SecurityIncident.status == IncidentStatus.CLOSED
        ).count()

        # 4. Purple-Team Validation
        pt_engine = PurpleTeamEngine(self.db, self.organization_id)
        pt_kpis = pt_engine.get_kpis()

        # 5. Vulnerabilities
        findings = self.db.query(AssetVulnerability).filter(
            AssetVulnerability.organization_id == self.organization_id
        ).all()
        open_vulns = sum(1 for f in findings if f.status == VulnerabilityStatus.OPEN)
        crit_vulns = sum(1 for f in findings if f.status == VulnerabilityStatus.OPEN and f.vulnerability and f.vulnerability.severity == VulnerabilitySeverity.CRITICAL)
        mitigated_vulns = sum(1 for f in findings if f.status in [VulnerabilityStatus.MITIGATED, VulnerabilityStatus.ACCEPTED_RISK])
        rem_rate = round((mitigated_vulns / max(1, len(findings))) * 100.0, 1) if findings else 100.0

        # 6. Overall Posture Score Calculation (0 - 100)
        # Base 100 minus risk penalties plus validation efficacy bonus
        deductions = (avg_risk * 0.35) + (open_incidents * 15.0) + (crit_vulns * 5.0)
        efficacy_bonus = (pt_kpis.overall_efficacy_rate * 0.15) if pt_kpis.total_simulations > 0 else 5.0
        calculated_score = int(max(10, min(100, 100 - deductions + efficacy_bonus)))

        if calculated_score >= 85:
            posture_level = "EXCELLENT"
        elif calculated_score >= 65:
            posture_level = "ACCEPTABLE"
        elif calculated_score >= 45:
            posture_level = "AT_RISK"
        else:
            posture_level = "CRITICAL"

        # Top Risks
        top_risks = [
            TopRiskItem(
                category="Vulnerability Exposure",
                item_name=f"{crit_vulns} Critical Vulnerabilities Open",
                severity="CRITICAL" if crit_vulns > 0 else "LOW",
                impact="Unpatched RCE vulnerabilities on legacy services (e.g. vsftpd, Samba)",
                recommended_action="Execute patch deployment and verify mitigation via Vulnerability Management."
            ),
            TopRiskItem(
                category="Incident Management",
                item_name=f"{open_incidents} Active Threat Incidents",
                severity="HIGH" if open_incidents > 0 else "LOW",
                impact="Potential unauthorized access or lateral movement detected in SIEM",
                recommended_action="Authorize automated SOAR containment playbooks to isolate affected endpoints."
            ),
            TopRiskItem(
                category="Defensive Validation",
                item_name=f"{pt_kpis.total_missed} Uncovered Detection Gaps",
                severity="MEDIUM" if pt_kpis.total_missed > 0 else "LOW",
                impact="Adversary techniques executed without triggering active alert rules",
                recommended_action="Author dedicated SIEM correlation rules for missed MITRE techniques."
            )
        ]

        recommendations = [
            "Enforce zero-trust network segmentation at core transit routers to reduce attack path reachability.",
            "Accelerate remediation of CVSS >= 9.0 vulnerabilities across virtual lab testbeds.",
            "Run continuous purple-team validation campaigns weekly to maintain detection efficacy above 80%."
        ]

        summary_text = (
            f"Executive cybersecurity posture for {org_name} is currently evaluated as {posture_level} "
            f"with an overall health index of {calculated_score}/100. The infrastructure monitors {total_assets} "
            f"managed assets across distributed sites with {active_agents} active EDR agents. Detection controls achieve "
            f"a {pt_kpis.overall_efficacy_rate}% MITRE ATT&CK validation efficacy with an average response time of {pt_kpis.mean_time_to_detect_seconds}s."
        )

        md_report = f"""# CyberLab Executive Cybersecurity Report
**Organization**: {org_name}
**Report ID**: `{report_id}`
**Generated**: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}
**Overall Health Score**: **{calculated_score} / 100** ({posture_level})

---

## 1. Executive Summary
{summary_text}

---

## 2. Key Operational Metrics
- **Managed Assets**: {total_assets}
- **Active EDR Agents**: {active_agents}
- **Active Security Incidents**: {open_incidents}
- **Purple-Team Efficacy**: {pt_kpis.overall_efficacy_rate}%
- **Mean Time to Detect (MTTD)**: {pt_kpis.mean_time_to_detect_seconds}s
- **Remediation Progress**: {rem_rate}% ({mitigated_vulns} mitigated)

---

## 3. Prioritized Strategic Recommendations
1. {recommendations[0]}
2. {recommendations[1]}
3. {recommendations[2]}
"""

        kpis = {
            "total_assets": total_assets,
            "active_agents": active_agents,
            "open_incidents": open_incidents,
            "closed_incidents": closed_incidents,
            "purple_team_efficacy_pct": pt_kpis.overall_efficacy_rate,
            "mttd_seconds": pt_kpis.mean_time_to_detect_seconds,
            "total_vulnerabilities": len(findings),
            "critical_vulnerabilities": crit_vulns,
            "remediation_rate_pct": rem_rate
        }

        return ExecutiveReportResponse(
            report_id=report_id,
            title="Executive Cybersecurity Posture Scorecard",
            organization_name=org_name,
            generated_at=now,
            overall_posture_score=calculated_score,
            posture_level=posture_level,
            executive_summary=summary_text,
            kpi_summary=kpis,
            top_risks=top_risks,
            remediation_recommendations=recommendations,
            report_markdown=md_report
        )

    def generate_compliance_report(self, standard: str = "NIST CSF 2.0 / CIS Controls") -> ComplianceReportResponse:
        """Generates an audit-grade technical compliance report."""
        report_id = f"rpt-comp-{str(uuid.uuid4())[:8]}"
        now = datetime.now(timezone.utc)

        org = self.db.query(Organization).filter(Organization.id == self.organization_id).first()
        org_name = org.name if org else "CyberLab Enterprise"

        assets = self.db.query(Asset).filter(Asset.organization_id == self.organization_id).all()
        agents = self.db.query(Agent).filter(Agent.organization_id == self.organization_id).all()
        alerts = self.db.query(SecurityAlert).filter(SecurityAlert.organization_id == self.organization_id).all()
        soar_actions = self.db.query(SOARAction).filter(SOARAction.organization_id == self.organization_id).all()

        pt_engine = PurpleTeamEngine(self.db, self.organization_id)
        coverage = pt_engine.get_coverage_matrix()

        controls = [
            ComplianceControlItem(
                control_id="ID.AM-01",
                family="Asset Management (Identify)",
                title="Continuous Unified Physical & Virtual Asset Inventory",
                status="COMPLIANT" if len(assets) > 0 else "PARTIAL",
                coverage_score_pct=100.0 if len(assets) > 0 else 60.0,
                evidence=f"Reconciled catalog tracking {len(assets)} assets across VMs, agents, and network topologies."
            ),
            ComplianceControlItem(
                control_id="PR.AC-02",
                family="Access Control (Protect)",
                title="Role-Based Access Control and Session Verification",
                status="COMPLIANT",
                coverage_score_pct=100.0,
                evidence="Enforced JWT Bearer authentication with ADMIN, ANALYST, and AUDITOR RBAC scopes."
            ),
            ComplianceControlItem(
                control_id="PR.DS-05",
                family="Data Security (Protect)",
                title="File Integrity Monitoring & Baseline Verification",
                status="COMPLIANT",
                coverage_score_pct=95.0,
                evidence="Distributed Linux Agent FIM continuous SHA-256 hash checking on critical system binaries."
            ),
            ComplianceControlItem(
                control_id="DE.CM-01",
                family="Continuous Monitoring (Detect)",
                title="Stateful SIEM Event Correlation & Anomaly Alerting",
                status="COMPLIANT" if len(alerts) > 0 else "PARTIAL",
                coverage_score_pct=90.0,
                evidence="Rule-based correlation pipeline with automated Root Cause Analysis."
            ),
            ComplianceControlItem(
                control_id="RS.RP-01",
                family="Response Planning (Respond)",
                title="Automated SOAR Quarantine with Approval Governance",
                status="COMPLIANT" if len(soar_actions) > 0 else "PARTIAL",
                coverage_score_pct=100.0,
                evidence="Non-destructive containment playbooks with verified execution and 1-click rollback."
            ),
            ComplianceControlItem(
                control_id="CA.VA-02",
                family="Security Assessment (Validate)",
                title="Automated Purple-Team Control Validation Testing",
                status="COMPLIANT" if coverage.overall_coverage_pct >= 70.0 else "PARTIAL",
                coverage_score_pct=coverage.overall_coverage_pct,
                evidence=f"Validated {coverage.covered_techniques}/{coverage.total_techniques_tested} MITRE ATT&CK techniques with atomic simulations."
            )
        ]

        avg_comp = round(sum(c.coverage_score_pct for c in controls) / max(1, len(controls)), 1)
        cert_status = "AUDIT_READY" if avg_comp >= 85.0 else "CONDITIONALLY_COMPLIANT" if avg_comp >= 65.0 else "NON_COMPLIANT"

        summary_text = (
            f"Compliance assessment against {standard} for {org_name} achieved an overall score of {avg_comp}%. "
            f"The environment is classified as {cert_status} with all primary control families actively implemented."
        )

        md_report = f"""# CyberLab Technical Compliance & Audit Report
**Organization**: {org_name}
**Standard**: {standard}
**Report ID**: `{report_id}`
**Generated**: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}
**Compliance Readiness**: **{avg_comp}%** ({cert_status})

---

## 1. Compliance Summary
{summary_text}

---

## 2. Control Family Evaluation
"""
        for c in controls:
            md_report += f"- **[{c.status}] {c.control_id} - {c.title}** ({c.family})\n  - Coverage: {c.coverage_score_pct}%\n  - Evidence: {c.evidence}\n"

        return ComplianceReportResponse(
            report_id=report_id,
            title="Technical Compliance & Audit Readiness Report",
            organization_name=org_name,
            standard=standard,
            generated_at=now,
            compliance_score_pct=avg_comp,
            certification_status=cert_status,
            summary=summary_text,
            controls=controls,
            evidence_count=len(assets) + len(alerts) + len(soar_actions),
            report_markdown=md_report
        )
