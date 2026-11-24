"""
Tests for Unified Asset Inventory & Risk Posture Engine (Phase 5)
Verifies multi-source asset synchronization, dynamic risk scoring, filtering, and RBAC governance.
"""
import json
import pytest
from app.models.organization import Organization
from app.models.vm import VirtualMachine, PowerState
from app.models.agent import Agent, AgentStatus, AgentTelemetry
from app.models.device import NetworkDevice, DeviceType
from app.models.topology import Topology
from app.models.asset import Asset, AssetType, AssetCriticality, AssetStatus


@pytest.fixture
def synced_assets(client, admin_token, db):
    """Fixture that seeds multi-source entities and synchronizes them into unified Assets."""
    org = db.query(Organization).first()
    org_id = org.id if org else "default-org"

    # 1. Seed a vulnerable target VM
    vm = VirtualMachine(
        organization_id=org_id,
        name="Metasploitable2-Linux",
        config_path="/vms/metasploitable2.vmx",
        power_state=PowerState.RUNNING,
        os_type="Ubuntu Linux 8.04",
        vcpus=1,
        memory_mb=512,
        is_vulnerable_target=True,
        network_adapters_json=json.dumps([{"name": "ethernet0", "is_bridged": False, "mac_address": "00:0C:29:4D:91:81"}])
    )
    db.add(vm)

    # 2. Seed a registered Linux Agent with telemetry
    agent = Agent(
        id="cl-agent-kali-01",
        organization_id=org_id,
        hostname="kali-security-node",
        ip_address="192.168.1.55",
        os_type="Linux",
        os_release="Kali Rolling 2026.3",
        kernel_version="7.2.15+kali",
        agent_version="0.4.0",
        status=AgentStatus.ONLINE,
        agent_token_hash="fake_hash",
        hardware_specs_json=json.dumps({"cpu_cores": 4, "memory_mb": 8192, "disk_total_gb": 120})
    )
    db.add(agent)
    db.flush()

    tel = AgentTelemetry(
        agent_id=agent.id,
        cpu_pct=15.0,
        memory_pct=35.0,
        disk_pct=40.0,
        network_connections_json=json.dumps([{"protocol": "tcp", "local_port": 22, "state": "LISTEN"}]),
        fim_alerts_json=json.dumps([{"path": "/etc/passwd", "action": "MODIFIED", "severity": "HIGH"}])
    )
    db.add(tel)

    # 3. Seed a simulated network topology device
    top = Topology(
        organization_id=org_id,
        name="DMZ Perimeter Topology",
        description="Perimeter security lab"
    )
    db.add(top)
    db.flush()

    dev = NetworkDevice(
        topology_id=top.id,
        name="perimeter-firewall-01",
        device_type="firewall",
        ip_address="10.0.0.1",
        status="RUNNING"
    )
    db.add(dev)
    db.commit()

    # Trigger sync
    sync_resp = client.post("/api/v1/assets/sync", headers={"Authorization": f"Bearer {admin_token}"})
    assert sync_resp.status_code == 200
    return sync_resp.json()


def test_asset_sync_multi_source(client, admin_token, db, synced_assets):
    """Verifies that the AssetManager harmonizes VMs, Agents, and Simulated Devices into a single index."""
    assert synced_assets["total_synced"] == 3
    assert synced_assets["vm_assets_synced"] == 1
    assert synced_assets["agent_assets_synced"] == 1
    assert synced_assets["simulated_assets_synced"] == 1

    # Verify records in database
    assets = db.query(Asset).all()
    assert len(assets) == 3

    # Check Metasploitable risk score calculation (base 10 + vulnerable 55 + running 5 = 70)
    meta_asset = db.query(Asset).filter(Asset.name == "Metasploitable2-Linux").first()
    assert meta_asset is not None
    assert meta_asset.asset_type == AssetType.VIRTUAL_MACHINE
    assert meta_asset.risk_score >= 65
    assert "VULNERABLE_TARGET" in json.loads(meta_asset.security_tags_json)

    # Check Agent asset
    agent_asset = db.query(Asset).filter(Asset.name == "kali-security-node").first()
    assert agent_asset is not None
    assert agent_asset.asset_type == AssetType.AGENT_HOST
    assert "EDR_MONITORED" in json.loads(agent_asset.security_tags_json)
    assert "FIM_ALERT_ACTIVE" in json.loads(agent_asset.security_tags_json)


def test_asset_listing_and_filtering(client, admin_token, synced_assets):
    """Verifies search, filtering by type, and min_risk queries."""
    # 1. Filter by Asset Type
    resp_type = client.get("/api/v1/assets?asset_type=VIRTUAL_MACHINE", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_type.status_code == 200
    vms = resp_type.json()
    assert len(vms) >= 1
    assert all(a["asset_type"] == "VIRTUAL_MACHINE" for a in vms)

    # 2. Filter by min_risk threshold
    resp_risk = client.get("/api/v1/assets?min_risk=50", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_risk.status_code == 200
    high_risks = resp_risk.json()
    assert len(high_risks) >= 1
    assert all(a["risk_score"] >= 50 for a in high_risks)

    # 3. Search query
    resp_search = client.get("/api/v1/assets?search=firewall", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp_search.status_code == 200
    firewalls = resp_search.json()
    assert len(firewalls) >= 1
    assert any("firewall" in a["name"].lower() for a in firewalls)


def test_asset_kpis_and_aggregation(client, admin_token, synced_assets):
    """Verifies aggregated metrics and category counts."""
    resp = client.get("/api/v1/assets/kpis", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    kpis = resp.json()
    assert kpis["total_assets"] >= 3
    assert kpis["average_risk_score"] > 0
    assert "VIRTUAL_MACHINE" in kpis["by_type"]
    assert "AGENT_HOST" in kpis["by_type"]


def test_asset_criticality_update_lifecycle(client, admin_token, auditor_token, synced_assets):
    """Verifies that analysts can update business criticality and exposure with RBAC."""
    # Fetch first asset
    resp = client.get("/api/v1/assets", headers={"Authorization": f"Bearer {admin_token}"})
    asset_id = resp.json()[0]["id"]

    # Auditor cannot update
    resp_auditor = client.put(
        f"/api/v1/assets/{asset_id}/criticality",
        json={"criticality": "CRITICAL", "exposure": "DMZ"},
        headers={"Authorization": f"Bearer {auditor_token}"}
    )
    assert resp_auditor.status_code == 403

    # Admin updates successfully
    resp_admin = client.put(
        f"/api/v1/assets/{asset_id}/criticality",
        json={"criticality": "CRITICAL", "exposure": "DMZ"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp_admin.status_code == 200
    updated = resp_admin.json()
    assert updated["criticality"] == "CRITICAL"
    assert updated["exposure"] == "DMZ"
