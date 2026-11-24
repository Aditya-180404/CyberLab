"""
Tests for SOAR Execution, Approval Gates & Rollback Engine (Phase 7)
"""
import json
import pytest
from app.models.agent import Agent, AgentStatus
from app.models.soar import SOARPlaybook, SOARAction, ActionType, ActionStatus


@pytest.fixture
def test_agent_node(db):
    """Seeds an active agent for containment testing."""
    agent = Agent(
        id="cl-agent-target-99",
        organization_id="default-org",
        hostname="compromised-victim-box",
        ip_address="192.168.1.199",
        os_type="Linux",
        os_release="Ubuntu 22.04 LTS",
        status=AgentStatus.ONLINE,
        agent_token_hash="sample_hash",
        pending_commands_json=json.dumps([])
    )
    db.add(agent)
    db.commit()
    return agent


def test_list_playbooks_seeds_defaults(client, admin_token):
    """Verifies baseline containment playbooks are seeded and accessible."""
    resp = client.get("/api/v1/soar/playbooks", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    playbooks = resp.json()
    assert len(playbooks) >= 4
    pb_ids = [p["id"] for p in playbooks]
    assert "playbook-host-quarantine" in pb_ids
    assert "playbook-block-attacker-ip" in pb_ids


def test_playbook_execution_with_approval_gate(client, admin_token, auditor_token, test_agent_node, db):
    """Verifies that high-impact playbooks require human approval before execution."""
    payload = {
        "action_type": ActionType.ISOLATE_HOST,
        "target_type": "AGENT",
        "target_id": test_agent_node.id,
        "target_name": test_agent_node.hostname
    }

    # 1. Trigger Playbook
    resp_exec = client.post(
        "/api/v1/soar/playbooks/playbook-host-quarantine/execute",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp_exec.status_code == 200
    act = resp_exec.json()
    action_id = act["id"]
    assert act["status"] == ActionStatus.PENDING_APPROVAL
    assert act["verified"] is False

    # 2. Auditor lacks permission to approve
    resp_unauth = client.post(
        f"/api/v1/soar/actions/{action_id}/approve",
        headers={"Authorization": f"Bearer {auditor_token}"}
    )
    assert resp_unauth.status_code == 403

    # 3. Admin approves
    resp_approve = client.post(
        f"/api/v1/soar/actions/{action_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp_approve.status_code == 200
    approved_act = resp_approve.json()
    assert approved_act["status"] == ActionStatus.COMPLETED
    assert approved_act["verified"] is True
    assert approved_act["approved_by"] == "admin"

    # 4. Verify target agent received ISOLATE directive
    db.refresh(test_agent_node)
    assert test_agent_node.status == AgentStatus.ISOLATED
    cmds = json.loads(test_agent_node.pending_commands_json)
    assert "ISOLATE" in cmds


def test_playbook_automated_execution(client, admin_token):
    """Verifies automated playbooks execute immediately without approval gates."""
    payload = {
        "action_type": ActionType.BLOCK_IP,
        "target_type": "IP",
        "target_id": "198.51.100.44",
        "target_name": "attacker-c2"
    }

    resp = client.post(
        "/api/v1/soar/playbooks/playbook-block-attacker-ip/execute",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp.status_code == 200
    act = resp.json()
    assert act["status"] == ActionStatus.COMPLETED
    assert act["verified"] is True


def test_action_rejection(client, admin_token, test_agent_node):
    """Verifies rejecting a pending action updates status and records reason."""
    payload = {
        "action_type": ActionType.ISOLATE_HOST,
        "target_type": "AGENT",
        "target_id": test_agent_node.id
    }
    resp_exec = client.post(
        "/api/v1/soar/playbooks/playbook-host-quarantine/execute",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    action_id = resp_exec.json()["id"]

    resp_reject = client.post(
        f"/api/v1/soar/actions/{action_id}/reject",
        json={"reason": "False positive alert confirmed by SOC analyst."},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp_reject.status_code == 200
    rej = resp_reject.json()
    assert rej["status"] == ActionStatus.REJECTED
    assert "False positive" in rej["rejection_reason"]


def test_action_rollback_lifecycle(client, admin_token, test_agent_node, db):
    """Verifies rollback reverses containment state and restores host to ONLINE."""
    # 1. Execute and approve isolation
    payload = {
        "action_type": ActionType.ISOLATE_HOST,
        "target_type": "AGENT",
        "target_id": test_agent_node.id,
        "target_name": test_agent_node.hostname
    }
    resp_exec = client.post(
        "/api/v1/soar/playbooks/playbook-host-quarantine/execute",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    action_id = resp_exec.json()["id"]
    client.post(f"/api/v1/soar/actions/{action_id}/approve", headers={"Authorization": f"Bearer {admin_token}"})

    # 2. Rollback the action
    resp_rb = client.post(
        f"/api/v1/soar/actions/{action_id}/rollback",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp_rb.status_code == 200
    rb = resp_rb.json()
    assert rb["status"] == ActionStatus.ROLLED_BACK
    assert rb["is_rolled_back"] is True
    assert "admin" in rb["rollback_details"]

    # 3. Verify agent state is restored
    db.refresh(test_agent_node)
    assert test_agent_node.status == AgentStatus.ONLINE
    cmds = json.loads(test_agent_node.pending_commands_json)
    assert "RESTORE" in cmds


def test_soar_kpis(client, admin_token):
    """Verifies SOAR KPI counters accurately report status distributions."""
    resp = client.get("/api/v1/soar/kpis", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    kpis = resp.json()
    assert kpis["total_actions"] >= 0
    assert "by_type" in kpis
