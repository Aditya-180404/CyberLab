"""
Unit & Integration Tests for Network Simulation Engine (Phase 2)
"""
import pytest
from app.network.safety import HostProtectionValidator, HostProtectionError
from app.network.simulation_driver import SimulationDriver


def test_host_protection_blocks_physical_interfaces():
    """Ensures host physical and Wi-Fi interfaces are permanently protected."""
    with pytest.raises(HostProtectionError) as exc:
        HostProtectionValidator.validate_interface_name("wlan0")
    assert "CRITICAL SAFETY VIOLATION" in str(exc.value)

    with pytest.raises(HostProtectionError) as exc:
        HostProtectionValidator.validate_interface_name("eth0")
    assert "CRITICAL SAFETY VIOLATION" in str(exc.value)

    with pytest.raises(HostProtectionError) as exc:
        HostProtectionValidator.validate_interface_name("lo")
    assert "CRITICAL SAFETY VIOLATION" in str(exc.value)


def test_host_protection_requires_cyberlab_prefix():
    """Ensures created resources must use cl- or cl_ prefix."""
    with pytest.raises(HostProtectionError) as exc:
        HostProtectionValidator.validate_interface_name("my_custom_bridge")
    assert "SAFETY POLICY ENFORCEMENT" in str(exc.value)

    # Allowed prefix must pass
    HostProtectionValidator.validate_interface_name("cl-br-lan1")
    HostProtectionValidator.validate_interface_name("cl-ep-srv1")
    HostProtectionValidator.validate_namespace_name("cl-ns-dmz")


def test_simulation_driver_lifecycle():
    """Tests in-memory network resource provisioning, IP assignment, and teardown."""
    driver = SimulationDriver()

    # 1. Create bridge & namespace
    assert driver.create_bridge("cl-br-test", vlan_filtering=True) is True
    assert driver.create_namespace("cl-ns-node1") is True

    # 2. Create veth pair
    assert driver.create_veth_pair(
        endpoint_iface="cl-ep-node1",
        peer_iface="cl-brp-node1",
        namespace="cl-ns-node1",
        bridge_name="cl-br-test",
        ip_cidr="10.10.10.15/24",
        vlan_id=100
    ) is True

    # 3. Verify namespace inspection
    assert "cl-ep-node1" in driver.namespaces["cl-ns-node1"]["interfaces"]
    assert driver.namespaces["cl-ns-node1"]["ip_addresses"]["cl-ep-node1"] == "10.10.10.15/24"

    # 4. Configure route
    assert driver.configure_route("cl-ns-node1", "0.0.0.0/0", "10.10.10.1") is True
    assert len(driver.routes["cl-ns-node1"]) == 1

    # 5. IP conflict detection
    with pytest.raises(HostProtectionError) as exc:
        driver.create_veth_pair(
            endpoint_iface="cl-ep-node2",
            peer_iface="cl-brp-node2",
            namespace="cl-ns-node2",
            bridge_name="cl-br-test",
            ip_cidr="10.10.10.15/24"  # Duplicate IP
        )
    assert "IP address conflict" in str(exc.value)

    # 6. Delete resources
    assert driver.delete_veth_pair("cl-ep-node1") is True
    assert driver.delete_bridge("cl-br-test") is True
    assert driver.delete_namespace("cl-ns-node1") is True


def test_topology_api_crud_and_deployment(client, admin_token):
    """Tests topology creation, deployment preview, deployment execution, and teardown via REST API."""
    topology_payload = {
        "name": "Production DMZ Simulation",
        "description": "Multi-subnet isolated lab with simulated firewall and web server",
        "segments": [
            {
                "name": "DMZ Segment",
                "bridge_name": "cl-br-dmz",
                "vlan_id": 100,
                "cidr_block": "192.168.10.0/24",
                "gateway_ip": "192.168.10.1"
            }
        ],
        "devices": [
            {
                "name": "Web-Server-01",
                "device_type": "server",
                "namespace_name": "cl-ns-web01",
                "ip_address": "192.168.10.10"
            },
            {
                "name": "DMZ-Firewall",
                "device_type": "firewall",
                "namespace_name": "cl-ns-dmzfw",
                "ip_address": "192.168.10.1"
            }
        ],
        "connections": []
    }

    # 1. Create Topology
    create_res = client.post(
        "/api/v1/topologies",
        json=topology_payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert create_res.status_code == 201
    topo = create_res.json()
    topo_id = topo["id"]
    assert topo["status"] == "DRAFT"
    assert len(topo["devices"]) == 2
    assert len(topo["segments"]) == 1

    # 2. Preview Deployment
    prev_res = client.get(
        f"/api/v1/topologies/{topo_id}/preview",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert prev_res.status_code == 200
    preview = prev_res.json()
    assert preview["safety_check_passed"] is True
    assert "cl-br-dmz" in preview["bridges_to_create"]
    assert "cl-ns-web01" in preview["namespaces_to_create"]

    # 3. Deploy Topology
    deploy_res = client.post(
        f"/api/v1/topologies/{topo_id}/deploy",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert deploy_res.status_code == 200
    deploy_data = deploy_res.json()
    assert deploy_data["status"] == "DEPLOYED"

    # Verify status in database
    get_res = client.get(
        f"/api/v1/topologies/{topo_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_res.json()["status"] == "DEPLOYED"

    # 4. Teardown Topology
    teardown_res = client.post(
        f"/api/v1/topologies/{topo_id}/teardown",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert teardown_res.status_code == 200
    assert teardown_res.json()["status"] == "STOPPED"

    # 5. Delete Topology
    del_res = client.delete(
        f"/api/v1/topologies/{topo_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert del_res.status_code == 200


def test_analyst_cannot_deploy_topology(client, analyst_token):
    """SOC Analyst role does not possess permission to deploy network changes."""
    deploy_res = client.post(
        "/api/v1/topologies/dummy-topology-id/deploy",
        headers={"Authorization": f"Bearer {analyst_token}"}
    )
    assert deploy_res.status_code == 403
    assert "Operation not permitted" in deploy_res.json()["detail"]
