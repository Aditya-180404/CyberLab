"""
Tests for SIEM, Detection Engine & MITRE ATT&CK Mapping (Phase 6)
Verifies event ingestion, rule evaluation, alert aggregation, incident correlation, and MITRE heatmap.
"""
import pytest
from app.models.siem import SecurityEvent, SecurityAlert, SecurityIncident, EventSeverity, AlertStatus, IncidentStatus


def test_event_ingestion_and_query(client, admin_token):
    """Verifies that normalized security events can be ingested and queried."""
    payload = {
        "category": "AUTHENTICATION",
        "severity": "LOW",
        "action": "SUCCESS",
        "message": "Accepted publickey for ghost from 192.168.1.100 port 52344 ssh2",
        "hostname": "kali-workstation",
        "source_ip": "192.168.1.100",
        "destination_ip": "192.168.1.105",
        "mitre_tactic": "Initial Access",
        "mitre_technique_id": "T1133",
        "mitre_technique_name": "External Remote Services"
    }

    # Ingest event
    resp = client.post("/api/v1/siem/events", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 201
    evt = resp.json()
    assert evt["id"].startswith("evt-")
    assert evt["message"] == payload["message"]
    assert evt["mitre_technique_id"] == "T1133"

    # Query event stream
    list_resp = client.get("/api/v1/siem/events", headers={"Authorization": f"Bearer {admin_token}"})
    assert list_resp.status_code == 200
    events = list_resp.json()
    assert any(e["id"] == evt["id"] for e in events)


def test_brute_force_detection_rule(client, admin_token, db):
    """Verifies that 3 consecutive failed logins trigger RULE_AUTH_BRUTE_FORCE."""
    target_host = "metasploitable2-target"
    attacker_ip = "192.168.1.99"

    # Ingest 3 failed logins
    for i in range(3):
        client.post(
            "/api/v1/siem/events",
            json={
                "category": "AUTHENTICATION",
                "severity": "LOW",
                "action": "FAILURE",
                "message": f"Failed password for invalid user admin{i} from {attacker_ip} ssh2",
                "hostname": target_host,
                "source_ip": attacker_ip
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

    # Check that alert was triggered
    alerts_resp = client.get("/api/v1/siem/alerts", headers={"Authorization": f"Bearer {admin_token}"})
    assert alerts_resp.status_code == 200
    alerts = alerts_resp.json()
    bf_alert = next((a for a in alerts if a["rule_id"] == "RULE_AUTH_BRUTE_FORCE"), None)
    assert bf_alert is not None
    assert bf_alert["mitre_technique_id"] == "T1110"
    assert bf_alert["hostname"] == target_host


def test_incident_correlation_multi_stage(client, admin_token, db):
    """Verifies that 2 distinct threat vectors on the same host trigger an automated SecurityIncident."""
    target = "victim-server-01"

    # 1. Trigger Brute Force (3 failed logins)
    for i in range(3):
        client.post(
            "/api/v1/siem/events",
            json={
                "category": "AUTHENTICATION",
                "severity": "LOW",
                "action": "FAILURE",
                "message": f"Failed password for user root from 10.0.0.99 ssh2 attempt {i}",
                "hostname": target,
                "source_ip": "10.0.0.99"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )

    # 2. Trigger Sudo Privilege Escalation on same host
    client.post(
        "/api/v1/siem/events",
        json={
            "category": "AUTHENTICATION",
            "severity": "HIGH",
            "action": "FAILURE",
            "message": "sudo: user 'www-data' : 3 incorrect password attempts ; USER=root ; COMMAND=/bin/bash (privilege escalation)",
            "hostname": target,
            "source_ip": "10.0.0.99"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    # Verify correlated incident is created
    inc_resp = client.get("/api/v1/siem/incidents", headers={"Authorization": f"Bearer {admin_token}"})
    assert inc_resp.status_code == 200
    incidents = inc_resp.json()
    assert len(incidents) >= 1
    inc = next((i for i in incidents if i["primary_hostname"] == target), None)
    assert inc is not None
    assert inc["alert_count"] >= 2
    assert "Credential Access" in inc["mitre_tactics"]
    assert "Privilege Escalation" in inc["mitre_tactics"]


def test_attack_simulation_and_mitre_matrix(client, admin_token):
    """Verifies the attack simulator generates events and updates the MITRE ATT&CK Matrix."""
    # Run reverse shell simulation
    sim_resp = client.post(
        "/api/v1/siem/simulate",
        json={"scenario": "reverse_shell", "target_hostname": "test-box-01"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert sim_resp.status_code == 200
    events = sim_resp.json()
    assert len(events) >= 1

    # Check alert was generated
    alerts_resp = client.get("/api/v1/siem/alerts", headers={"Authorization": f"Bearer {admin_token}"})
    assert any(a["rule_id"] == "RULE_SUSPICIOUS_REVERSE_SHELL" for a in alerts_resp.json())

    # Check MITRE Matrix
    mitre_resp = client.get("/api/v1/siem/mitre", headers={"Authorization": f"Bearer {admin_token}"})
    assert mitre_resp.status_code == 200
    data = mitre_resp.json()
    assert data["active_techniques_triggered"] >= 1
    assert "Execution" in data["tactics"]
    exec_techs = data["tactics"]["Execution"]
    shell_tech = next((t for t in exec_techs if t["technique_id"] == "T1059.004"), None)
    assert shell_tech is not None
    assert shell_tech["event_count"] >= 1


def test_siem_kpis(client, admin_token):
    """Verifies SIEM KPI counters reflect ingested telemetry."""
    # Ingest a sample event first
    client.post(
        "/api/v1/siem/events",
        json={
            "category": "SYSTEM_LOG",
            "severity": "LOW",
            "action": "DETECTED",
            "message": "Cron job execution started: backup.sh",
            "hostname": "backup-server"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    kpi_resp = client.get("/api/v1/siem/kpis", headers={"Authorization": f"Bearer {admin_token}"})
    assert kpi_resp.status_code == 200
    kpis = kpi_resp.json()
    assert kpis["total_events"] > 0
    assert "SYSTEM_LOG" in kpis["by_category"]
