"""
Unit & Integration Tests for Purple-Team Validation & Attack Simulation (Phase 9)
Verifies scenario catalog, atomic simulation execution, SIEM detection correlation,
coverage gap analysis, and REST API endpoints.
"""
import pytest
from app.purple_team.engine import PurpleTeamEngine
from app.models.purple_team import DetectionStatus, SimulationStatus
from app.models.user import User


def test_purple_team_scenario_seeding(db):
    """Verify default atomic purple team scenarios are seeded and listable."""
    admin_user = db.query(User).filter_by(username="admin").first()
    engine = PurpleTeamEngine(db, admin_user.organization_id)

    scenarios = engine.get_scenarios()
    assert len(scenarios) >= 6
    
    ids = {s.id for s in scenarios}
    assert "scen-t1110-brute-force" in ids
    assert "scen-t1548-sudo-abuse" in ids
    assert "scen-t1003-shadow-dump" in ids
    assert "scen-t1082-sysinfo" in ids


def test_execute_scenario_detected(db):
    """Verify that simulating an attack with a matching rule results in DETECTED status."""
    admin_user = db.query(User).filter_by(username="admin").first()
    engine = PurpleTeamEngine(db, admin_user.organization_id)

    # Execute Sudo Abuse simulation (mapped to RULE_PRIVILEGE_ESCALATION_SUDO)
    execution = engine.execute_scenario(
        scenario_id="scen-t1548-sudo-abuse",
        executed_by="test-analyst"
    )

    assert execution.status == SimulationStatus.COMPLETED
    assert execution.validation_result is not None
    assert execution.validation_result.detection_status == DetectionStatus.DETECTED
    assert execution.validation_result.matched_alert_id is not None
    assert execution.validation_result.matched_rule_id == "RULE_PRIVILEGE_ESCALATION_SUDO"


def test_execute_scenario_gap_missed(db):
    """Verify that a probe without a detection rule results in MISSED status (Detection Gap)."""
    admin_user = db.query(User).filter_by(username="admin").first()
    engine = PurpleTeamEngine(db, admin_user.organization_id)

    # Execute benign sysinfo probe (no SIEM alert rule)
    execution = engine.execute_scenario(
        scenario_id="scen-t1082-sysinfo",
        executed_by="test-analyst"
    )

    assert execution.status == SimulationStatus.COMPLETED
    assert execution.validation_result is not None
    assert execution.validation_result.detection_status == DetectionStatus.MISSED
    assert execution.validation_result.matched_alert_id is None


def test_run_purple_team_campaign(db):
    """Verify batch execution of purple team campaign and efficacy rate calculation."""
    admin_user = db.query(User).filter_by(username="admin").first()
    engine = PurpleTeamEngine(db, admin_user.organization_id)

    campaign_res = engine.run_campaign(executed_by="test-runner")
    assert campaign_res.total_scenarios_executed >= 6
    assert campaign_res.detected_count > 0
    assert campaign_res.efficacy_rate_pct > 0.0
    assert len(campaign_res.executions) == campaign_res.total_scenarios_executed


def test_mitre_coverage_matrix(db):
    """Verify MITRE coverage response and gap categorization."""
    admin_user = db.query(User).filter_by(username="admin").first()
    engine = PurpleTeamEngine(db, admin_user.organization_id)

    coverage = engine.get_coverage_matrix()
    assert coverage.total_techniques_tested >= 6
    assert coverage.covered_techniques > 0
    assert len(coverage.coverage_items) >= 6

    statuses = {item.coverage_status for item in coverage.coverage_items}
    assert "COVERED" in statuses or "GAP" in statuses


def test_purple_team_kpis(db):
    """Verify Purple Team efficacy KPI calculations."""
    admin_user = db.query(User).filter_by(username="admin").first()
    engine = PurpleTeamEngine(db, admin_user.organization_id)

    # Run at least one detected scenario
    engine.execute_scenario("scen-t1548-sudo-abuse", executed_by="admin")

    kpis = engine.get_kpis()
    assert kpis.total_simulations >= 1
    assert kpis.total_detected >= 1
    assert kpis.overall_efficacy_rate >= 0.0


def test_purple_team_api_endpoints(client, admin_token):
    """Verify HTTP REST API endpoints."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. GET /api/v1/purple-team/scenarios
    res = client.get("/api/v1/purple-team/scenarios", headers=headers)
    assert res.status_code == 200
    scenarios = res.json()
    assert len(scenarios) >= 6

    # 2. POST /api/v1/purple-team/execute
    exec_payload = {"scenario_id": "scen-t1548-sudo-abuse"}
    exec_res = client.post("/api/v1/purple-team/execute", json=exec_payload, headers=headers)
    assert exec_res.status_code == 200
    exec_data = exec_res.json()
    assert exec_data["status"] == "COMPLETED"
    assert exec_data["validation_result"]["detection_status"] == "DETECTED"

    # 3. GET /api/v1/purple-team/executions
    list_res = client.get("/api/v1/purple-team/executions", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 4. GET /api/v1/purple-team/coverage
    cov_res = client.get("/api/v1/purple-team/coverage", headers=headers)
    assert cov_res.status_code == 200
    assert cov_res.json()["total_techniques_tested"] >= 6

    # 5. GET /api/v1/purple-team/kpis
    kpi_res = client.get("/api/v1/purple-team/kpis", headers=headers)
    assert kpi_res.status_code == 200
    assert kpi_res.json()["total_simulations"] >= 1
