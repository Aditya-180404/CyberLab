"""
End-to-End Test for Standalone Linux Agent
Executes CyberLabAgent directly against test server to verify live registration,
heartbeat exchange, telemetry ingestion, and SOAR command handling.
"""
import sys
import os
import json
import pytest

# Add project root so agent module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from agent.cyberlab_agent import CyberLabAgent
from app.models.agent import Agent, AgentStatus, AgentTelemetry


def test_agent_e2e_lifecycle(client, db, tmp_path):
    """Simulates real agent execution cycle using mock HTTP handler."""
    cfg_file = str(tmp_path / "test_agent_config.json")
    agent = CyberLabAgent(server_url="http://testserver", config_path=cfg_file)

    # Monkeypatch agent's _http_request to route through FastAPI TestClient
    def mock_http(endpoint: str, data=None):
        headers = {}
        if agent.agent_token and agent.agent_id:
            headers["Authorization"] = f"Bearer {agent.agent_token}"
            headers["X-CyberLab-Agent-ID"] = agent.agent_id

        if data is not None:
            res = client.post(endpoint, json=data, headers=headers)
        else:
            res = client.get(endpoint, headers=headers)

        if res.status_code >= 400:
            raise Exception(f"HTTP {res.status_code}: {res.text}")
        return res.json()

    agent._http_request = mock_http

    # 1. Register agent
    success = agent.register()
    assert success is True
    assert agent.agent_id is not None
    assert agent.agent_token is not None
    assert os.path.exists(cfg_file)

    # Verify baseline in DB
    db_agent = db.query(Agent).filter(Agent.id == agent.agent_id).first()
    assert db_agent is not None
    assert db_agent.status == AgentStatus.ONLINE

    # 2. Baseline FIM hashing
    test_fim_file = tmp_path / "test_hosts"
    test_fim_file.write_text("127.0.0.1 localhost\n")
    agent.policy["fim_monitored_paths"] = [str(test_fim_file)]
    agent.compute_fim_baselines()
    assert str(test_fim_file) in agent.fim_baselines

    # 3. Send Heartbeat
    agent.send_heartbeat()
    assert agent.is_isolated is False

    # 4. Send Telemetry
    agent.send_telemetry()
    db.refresh(db_agent)
    telemetry_recs = db.query(AgentTelemetry).filter(AgentTelemetry.agent_id == agent.agent_id).all()
    assert len(telemetry_recs) == 1
    assert telemetry_recs[0].cpu_pct >= 0.0

    # 5. Trigger FIM Change and detect delta
    test_fim_file.write_text("127.0.0.1 localhost rogue.cyberlab.local\n")
    deltas = agent.check_fim_deltas()
    assert len(deltas) == 1
    assert deltas[0]["action"] == "MODIFIED"
    assert deltas[0]["path"] == str(test_fim_file)

    # 6. Transmit delta telemetry to server
    agent.send_telemetry()
    telemetry_recs_2 = db.query(AgentTelemetry).filter(AgentTelemetry.agent_id == agent.agent_id).all()
    assert len(telemetry_recs_2) == 2
    # Check that latest telemetry record captured the FIM alert
    latest_rec = telemetry_recs_2[0] if telemetry_recs_2[0].created_at > telemetry_recs_2[1].created_at else telemetry_recs_2[1]
    assert str(test_fim_file) in latest_rec.fim_alerts_json

    # 7. Test SOAR Isolation Order
    db_agent.pending_commands_json = json.dumps(["ISOLATE"])
    db.commit()

    agent.send_heartbeat()
    assert agent.is_isolated is True

    # 8. Test SOAR Restoration Order
    db_agent.pending_commands_json = json.dumps(["RESTORE"])
    db.commit()

    agent.send_heartbeat()
    assert agent.is_isolated is False
