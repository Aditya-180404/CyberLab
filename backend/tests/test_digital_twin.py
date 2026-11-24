"""
Unit & Integration Tests for Digital Twin & Attack-Path Analysis (Phase 8)
Verifies NetworkX graph construction, attack path discovery, blast radius,
choke point centrality, and REST API endpoints.
"""
import pytest
from app.digital_twin.graph_engine import DigitalTwinGraphEngine
from app.models.asset import Asset, AssetType, AssetCriticality, AssetStatus
from app.models.user import User
from app.schemas.digital_twin import AttackPathRequest


def test_digital_twin_graph_construction(db):
    """Verify that graph engine constructs nodes, edges, zones, and summary statistics."""
    admin_user = db.query(User).filter_by(username="admin").first()
    assert admin_user is not None

    # Seed a test asset in DB
    asset = Asset(
        id="asset-test-web01",
        organization_id=admin_user.organization_id,
        name="Production Web Srv 01",
        asset_type=AssetType.VIRTUAL_MACHINE,
        criticality=AssetCriticality.HIGH,
        risk_score=70,
        exposure="DMZ",
        status=AssetStatus.ACTIVE
    )
    db.add(asset)
    db.commit()

    engine = DigitalTwinGraphEngine(db, admin_user.organization_id)
    graph_data = engine.get_graph_data()

    assert graph_data.summary.total_nodes >= 5
    assert graph_data.summary.total_edges >= 4
    assert graph_data.summary.critical_nodes >= 1

    node_ids = {n.id for n in graph_data.nodes}
    assert "node-adversary-ext-01" in node_ids
    assert "node-perimeter-fw-01" in node_ids
    assert "node-core-router-01" in node_ids
    assert "node-crown-jewel-db-vault" in node_ids
    assert "asset-test-web01" in node_ids


def test_attack_path_discovery(db):
    """Verify discovery of traversable attack paths between external adversary and crown jewel."""
    admin_user = db.query(User).filter_by(username="admin").first()
    engine = DigitalTwinGraphEngine(db, admin_user.organization_id)
    
    req = AttackPathRequest(
        source_node_id="node-adversary-ext-01",
        target_node_id="node-crown-jewel-db-vault",
        max_hops=6
    )
    res = engine.calculate_attack_paths(req)

    assert res.total_paths_found > 0
    assert res.shortest_path_hops >= 2
    
    path = res.paths[0]
    assert len(path.steps) == path.hops
    assert path.cumulative_risk > 0
    assert path.node_sequence[0] == "node-adversary-ext-01"
    assert path.node_sequence[-1] == "node-crown-jewel-db-vault"

    # Verify MITRE techniques are attached
    step_tactics = [s.tactic for s in path.steps]
    assert any("Initial Access" in t for t in step_tactics)
    assert any("Credential Access" in t or "Lateral Movement" in t for t in step_tactics)


def test_attack_path_invalid_node(db):
    """Verify error handling when a non-existent node ID is queried."""
    admin_user = db.query(User).filter_by(username="admin").first()
    engine = DigitalTwinGraphEngine(db, admin_user.organization_id)
    req = AttackPathRequest(
        source_node_id="non-existent-node-id",
        target_node_id="node-crown-jewel-db-vault"
    )
    with pytest.raises(ValueError) as excinfo:
        engine.calculate_attack_paths(req)
    assert "not found" in str(excinfo.value)


def test_blast_radius_calculation(db):
    """Verify downstream reachability and blast score calculation."""
    admin_user = db.query(User).filter_by(username="admin").first()
    engine = DigitalTwinGraphEngine(db, admin_user.organization_id)
    
    # Calculate blast radius from DMZ Web Proxy
    blast = engine.calculate_blast_radius("node-dmz-web-proxy-01")

    assert blast.node_id == "node-dmz-web-proxy-01"
    assert blast.total_reachable_nodes > 0
    assert blast.blast_score > 0
    assert blast.blast_score <= 100
    assert blast.playbook_to_execute is not None

    reachable_ids = {a.node_id for a in blast.reachable_assets}
    assert "node-core-router-01" in reachable_ids
    assert "node-crown-jewel-db-vault" in reachable_ids


def test_choke_point_identification(db):
    """Verify NetworkX centrality identification of defensive choke points."""
    admin_user = db.query(User).filter_by(username="admin").first()
    engine = DigitalTwinGraphEngine(db, admin_user.organization_id)
    choke_res = engine.identify_choke_points()

    assert len(choke_res.choke_points) > 0
    top_choke = choke_res.choke_points[0]
    assert top_choke.betweenness_centrality >= 0.0
    assert top_choke.suggested_action in ["ENFORCE_FIREWALL_FILTER", "DEPLOY_AGENT_EDR"]
    assert top_choke.zone in ["TRANSIT_ROUTER", "DMZ", "INTERNAL"]


def test_simulate_compromise_and_reset(db):
    """Verify dynamic what-if simulation toggle and reset."""
    admin_user = db.query(User).filter_by(username="admin").first()
    engine = DigitalTwinGraphEngine(db, admin_user.organization_id)
    initial_summary = engine.get_graph_data().summary
    initial_compromised = initial_summary.compromised_nodes

    # Simulate compromise on perimeter firewall
    DigitalTwinGraphEngine.set_simulated_compromise("node-perimeter-fw-01", True)
    engine_updated = DigitalTwinGraphEngine(db, admin_user.organization_id)
    updated_summary = engine_updated.get_graph_data().summary
    assert updated_summary.compromised_nodes == initial_compromised + 1

    # Reset
    DigitalTwinGraphEngine.clear_simulated_compromises()
    engine_reset = DigitalTwinGraphEngine(db, admin_user.organization_id)
    reset_summary = engine_reset.get_graph_data().summary
    assert reset_summary.compromised_nodes == initial_compromised


def test_digital_twin_api_endpoints(client, admin_token):
    """Verify full HTTP REST API endpoints."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. GET /api/v1/digital-twin/graph
    res = client.get("/api/v1/digital-twin/graph", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "edges" in data
    assert "summary" in data

    # 2. POST /api/v1/digital-twin/attack-paths
    path_payload = {
        "source_node_id": "node-adversary-ext-01",
        "target_node_id": "node-crown-jewel-db-vault",
        "max_hops": 6
    }
    path_res = client.post("/api/v1/digital-twin/attack-paths", json=path_payload, headers=headers)
    assert path_res.status_code == 200
    path_data = path_res.json()
    assert path_data["total_paths_found"] > 0
    assert len(path_data["paths"]) > 0

    # 3. GET /api/v1/digital-twin/blast-radius/{asset_id}
    blast_res = client.get("/api/v1/digital-twin/blast-radius/node-core-router-01", headers=headers)
    assert blast_res.status_code == 200
    blast_data = blast_res.json()
    assert blast_data["total_reachable_nodes"] > 0
    assert blast_data["blast_score"] > 0

    # 4. GET /api/v1/digital-twin/choke-points
    choke_res = client.get("/api/v1/digital-twin/choke-points", headers=headers)
    assert choke_res.status_code == 200
    choke_data = choke_res.json()
    assert len(choke_data["choke_points"]) > 0

    # 5. POST /api/v1/digital-twin/simulate-compromise
    sim_res = client.post(
        "/api/v1/digital-twin/simulate-compromise",
        json={"node_id": "node-core-router-01", "compromised": True},
        headers=headers
    )
    assert sim_res.status_code == 200
    assert sim_res.json()["is_compromised"] is True

    # 6. POST /api/v1/digital-twin/reset-simulation
    reset_res = client.post("/api/v1/digital-twin/reset-simulation", headers=headers)
    assert reset_res.status_code == 200
    assert reset_res.json()["status"] == "SUCCESS"
