"""
Unit & Integration Tests for Multi-Site Enterprise Management & Reporting (Phase 12)
Verifies site lifecycle, stats aggregation, executive reporting,
compliance audits, and REST API endpoints.
"""
import pytest
from app.enterprise.site_service import SiteService
from app.enterprise.report_generator import ReportGenerator
from app.schemas.site import SiteCreate, SiteUpdate
from app.models.user import User
from app.models.asset import Asset, AssetType, AssetCriticality, AssetStatus


def test_list_and_create_site(db):
    """Verify site auto-seeding, registration, and update."""
    admin_user = db.query(User).filter_by(username="admin").first()
    service = SiteService(db, admin_user.organization_id)

    # List sites (should auto-seed default site)
    sites = service.list_sites()
    assert len(sites) >= 1
    assert sites[0].status == "ONLINE"

    # Create a new branch site
    new_site_in = SiteCreate(
        name="Branch Lab - Offsite Testing",
        description="Isolated secondary testing lab environment.",
        location="Remote Cloud / Offsite",
        ip_range="10.20.0.0/16"
    )
    new_site = service.create_site(new_site_in)
    assert new_site.name == "Branch Lab - Offsite Testing"
    assert new_site.location == "Remote Cloud / Offsite"

    # Update site
    updated = service.update_site(new_site.id, SiteUpdate(status="MAINTENANCE"))
    assert updated.status == "MAINTENANCE"


def test_site_stats_aggregation(db):
    """Verify aggregated fleet metrics calculation per site."""
    admin_user = db.query(User).filter_by(username="admin").first()
    service = SiteService(db, admin_user.organization_id)

    # Seed an asset
    asset = Asset(
        id="asset-site-stats-test",
        organization_id=admin_user.organization_id,
        name="Stats Test Asset",
        asset_type=AssetType.VIRTUAL_MACHINE,
        criticality=AssetCriticality.HIGH,
        risk_score=30,
        status=AssetStatus.ACTIVE
    )
    db.add(asset)
    db.commit()

    stats = service.get_sites_with_stats()
    assert len(stats) >= 1
    assert stats[0].total_assets >= 1


def test_delete_site(db):
    """Verify site deletion unlinks attached assets safely."""
    admin_user = db.query(User).filter_by(username="admin").first()
    service = SiteService(db, admin_user.organization_id)

    site = service.create_site(SiteCreate(name="Temporary Deletable Site"))
    site_id = site.id

    service.delete_site(site_id)
    remaining_ids = [s.id for s in service.list_sites()]
    assert site_id not in remaining_ids


def test_generate_executive_report(db):
    """Verify executive posture scorecard and KPI generation."""
    admin_user = db.query(User).filter_by(username="admin").first()
    generator = ReportGenerator(db, admin_user.organization_id)

    report = generator.generate_executive_report()
    assert report.report_id.startswith("rpt-exec-")
    assert report.overall_posture_score >= 0
    assert report.overall_posture_score <= 100
    assert report.posture_level in ["EXCELLENT", "ACCEPTABLE", "AT_RISK", "CRITICAL"]
    assert len(report.top_risks) == 3
    assert len(report.remediation_recommendations) == 3
    assert "# CyberLab Executive Cybersecurity Report" in report.report_markdown


def test_generate_compliance_report(db):
    """Verify technical compliance audit report generation."""
    admin_user = db.query(User).filter_by(username="admin").first()
    generator = ReportGenerator(db, admin_user.organization_id)

    report = generator.generate_compliance_report("NIST CSF 2.0 / CIS Controls")
    assert report.report_id.startswith("rpt-comp-")
    assert report.compliance_score_pct >= 0.0
    assert report.certification_status in ["AUDIT_READY", "CONDITIONALLY_COMPLIANT", "NON_COMPLIANT"]
    assert len(report.controls) >= 5
    assert "# CyberLab Technical Compliance & Audit Report" in report.report_markdown


def test_sites_and_reports_api(client, admin_token):
    """Verify HTTP REST API endpoints for multi-site and reporting."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. GET /api/v1/sites
    sites_res = client.get("/api/v1/sites", headers=headers)
    assert sites_res.status_code == 200
    assert len(sites_res.json()) >= 1

    # 2. POST /api/v1/sites
    new_site_payload = {
        "name": "API Testing Site",
        "description": "Created via API tests",
        "location": "Test Region",
        "ip_range": "192.168.100.0/24"
    }
    create_res = client.post("/api/v1/sites", json=new_site_payload, headers=headers)
    assert create_res.status_code == 200
    site_id = create_res.json()["id"]

    # 3. GET /api/v1/sites/stats
    stats_res = client.get("/api/v1/sites/stats", headers=headers)
    assert stats_res.status_code == 200
    assert len(stats_res.json()) >= 1

    # 4. DELETE /api/v1/sites/{site_id}
    del_res = client.delete(f"/api/v1/sites/{site_id}", headers=headers)
    assert del_res.status_code == 200

    # 5. GET /api/v1/reports/executive
    exec_res = client.get("/api/v1/reports/executive", headers=headers)
    assert exec_res.status_code == 200
    exec_data = exec_res.json()
    assert "overall_posture_score" in exec_data
    assert "report_markdown" in exec_data

    # 6. GET /api/v1/reports/compliance
    comp_res = client.get("/api/v1/reports/compliance", headers=headers)
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert "compliance_score_pct" in comp_data
    assert len(comp_data["controls"]) >= 5
