"""
Tests for Distributed Linux Agent Platform (Phase 4)
Verifies registration, heartbeat, telemetry ingestion, SOAR isolation, and revocation.
"""
import pytest
from app.models.agent import AgentStatus


def test_agent_registration_flow(client):
    """Verifies that an agent can register and obtain credentials and default policy."""
    payload = {
        "hostname": "kali-workstation",
        "ip_address": "192.168.1.105",
        "os_type": "Linux",
        "os_release": "Kali GNU/Linux Rolling 2026.3",
        "kernel_version": "7.2.15+kali-amd64",
        "agent_version": "1.0.0",
        "hardware_specs": {
            "cpu_cores": 8,
            "memory_mb": 16384,
            "disk_total_gb": 500
        }
    }
    response = client.post("/api/v1/agents/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "agent_id" in data
    assert data["agent_id"].startswith("cl-agent-")
    assert "agent_token" in data
    assert data["agent_token"].startswith("cla_")
    assert data["heartbeat_interval_sec"] == 10
    assert "policy" in data
    assert "/etc/passwd" in data["policy"]["fim_monitored_paths"]


def test_agent_heartbeat_and_auth(client):
    """Verifies agent authentication and heartbeat status updates."""
    # Register first
    reg = client.post(
        "/api/v1/agents/register",
        json={"hostname": "parrot-sec", "ip_address": "192.168.1.110", "agent_version": "1.0.0"}
    )
    assert reg.status_code == 201
    agent_id = reg.json()["agent_id"]
    token = reg.json()["agent_token"]

    # 1. Unauthenticated heartbeat should fail
    resp_unauth = client.post("/api/v1/agents/heartbeat", json={"status": "ONLINE"})
    assert resp_unauth.status_code == 401

    # 2. Authenticated heartbeat
    headers = {
        "Authorization": f"Bearer {token}",
        "X-CyberLab-Agent-ID": agent_id
    }
    resp_hb = client.post("/api/v1/agents/heartbeat", json={"status": "ONLINE"}, headers=headers)
    assert resp_hb.status_code == 200
    hb_data = resp_hb.json()
    assert hb_data["status"] == "ONLINE"
    assert hb_data["pending_commands"] == []


def test_agent_telemetry_ingestion(client):
    """Verifies that rich host telemetry can be securely ingested."""
    reg = client.post(
        "/api/v1/agents/register",
        json={"hostname": "metasploit-target", "ip_address": "192.168.1.120", "agent_version": "1.0.0"}
    )
    agent_id = reg.json()["agent_id"]
    token = reg.json()["agent_token"]

    headers = {
        "Authorization": f"Bearer {token}",
        "X-CyberLab-Agent-ID": agent_id
    }

    telemetry_payload = {
        "cpu_pct": 14.5,
        "memory_pct": 42.1,
        "disk_pct": 65.0,
        "network_connections": [
            {"protocol": "tcp", "local_port": 22, "state": "LISTEN"},
            {"protocol": "tcp", "local_port": 80, "state": "LISTEN"}
        ],
        "processes": [
            {"pid": 1, "name": "systemd", "cpu_pct": 0.1, "mem_pct": 0.2},
            {"pid": 1200, "name": "sshd", "cpu_pct": 0.0, "mem_pct": 0.4}
        ],
        "auth_events": [],
        "fim_alerts": [
            {"path": "/etc/passwd", "action": "MODIFIED", "severity": "HIGH", "message": "Hash changed"}
        ]
    }

    resp = client.post("/api/v1/agents/telemetry", json=telemetry_payload, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ingested"
    assert resp.json()["records"] == 2


def test_agent_listing_and_detail(client, admin_token):
    """Verifies that SOC analysts can list and inspect registered agents."""
    # Register an agent
    reg = client.post(
        "/api/v1/agents/register",
        json={"hostname": "web-srv-01", "ip_address": "10.0.0.50", "agent_version": "1.0.0"}
    )
    agent_id = reg.json()["agent_id"]
    token = reg.json()["agent_token"]

    # Send a telemetry packet
    client.post(
        "/api/v1/agents/telemetry",
        json={"cpu_pct": 25.0, "memory_pct": 55.0, "disk_pct": 30.0, "processes": [{"pid": 50, "name": "nginx"}]},
        headers={"Authorization": f"Bearer {token}", "X-CyberLab-Agent-ID": agent_id}
    )

    # Query agent list
    resp_list = client.get("/api/v1/agents", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_list.status_code == 200
    agents = resp_list.json()
    assert any(a["id"] == agent_id for a in agents)

    # Query agent detail
    resp_detail = client.get(f"/api/v1/agents/{agent_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_detail.status_code == 200
    detail = resp_detail.json()
    assert detail["hostname"] == "web-srv-01"
    assert detail["latest_telemetry"] is not None
    assert detail["latest_telemetry"]["cpu_pct"] == 25.0
    assert detail["latest_telemetry"]["processes_count"] == 1


def test_agent_isolation_and_restoration_lifecycle(client, admin_token):
    """Verifies the complete SOAR quarantine and restore cycle."""
    reg = client.post(
        "/api/v1/agents/register",
        json={"hostname": "compromised-node", "ip_address": "10.0.0.99", "agent_version": "1.0.0"}
    )
    agent_id = reg.json()["agent_id"]
    token = reg.json()["agent_token"]
    agent_headers = {"Authorization": f"Bearer {token}", "X-CyberLab-Agent-ID": agent_id}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Analyst triggers isolation
    iso_resp = client.post(f"/api/v1/agents/{agent_id}/isolate", headers=admin_headers)
    assert iso_resp.status_code == 200
    assert iso_resp.json()["status"] == AgentStatus.ISOLATED

    # 2. Agent checks in on heartbeat -> receives ISOLATE directive
    hb_resp = client.post("/api/v1/agents/heartbeat", json={"status": "ONLINE"}, headers=agent_headers)
    assert hb_resp.status_code == 200
    assert "ISOLATE" in hb_resp.json()["pending_commands"]

    # 3. Next heartbeat has no more pending commands (already dispatched)
    hb_resp2 = client.post("/api/v1/agents/heartbeat", json={"status": "ISOLATED"}, headers=agent_headers)
    assert hb_resp2.status_code == 200
    assert hb_resp2.json()["pending_commands"] == []

    # 4. Analyst restores host
    restore_resp = client.post(f"/api/v1/agents/{agent_id}/restore", headers=admin_headers)
    assert restore_resp.status_code == 200
    assert restore_resp.json()["status"] == AgentStatus.ONLINE

    # 5. Agent receives RESTORE directive
    hb_resp3 = client.post("/api/v1/agents/heartbeat", json={"status": "ISOLATED"}, headers=agent_headers)
    assert hb_resp3.status_code == 200
    assert "RESTORE" in hb_resp3.json()["pending_commands"]


def test_agent_credential_revocation(client, admin_token, auditor_token):
    """Verifies that revoked agents cannot communicate further and RBAC is enforced."""
    reg = client.post(
        "/api/v1/agents/register",
        json={"hostname": "rogue-agent", "ip_address": "10.0.0.66", "agent_version": "1.0.0"}
    )
    agent_id = reg.json()["agent_id"]
    token = reg.json()["agent_token"]

    # Auditor cannot isolate or revoke
    resp_perm = client.post(
        f"/api/v1/agents/{agent_id}/revoke",
        headers={"Authorization": f"Bearer {auditor_token}"}
    )
    assert resp_perm.status_code == 403

    # Admin revokes
    resp_revoke = client.post(
        f"/api/v1/agents/{agent_id}/revoke",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp_revoke.status_code == 200
    assert resp_revoke.json()["status"] == AgentStatus.REVOKED

    # Agent heartbeat is now blocked
    headers = {"Authorization": f"Bearer {token}", "X-CyberLab-Agent-ID": agent_id}
    resp_blocked = client.post("/api/v1/agents/heartbeat", json={"status": "ONLINE"}, headers=headers)
    assert resp_blocked.status_code in (401, 403)
