"""
Network Engine Orchestration Manager
Coordinates topology deployment, verification, teardown, and driver dispatching.
"""
import json
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.models.topology import Topology
from app.models.segment import NetworkSegment
from app.models.device import NetworkDevice
from app.models.connection import NetworkConnection
from app.models.audit import AuditLog
from app.schemas.network import DeploymentPreview, DeploymentResult
from app.network.driver_interface import NetworkDriver
from app.network.simulation_driver import SimulationDriver
from app.network.linux_driver import LinuxKernelDriver
from app.network.safety import HostProtectionValidator, HostProtectionError

logger = logging.getLogger("cyberlab.network.manager")


class NetworkEngineManager:
    def __init__(self, driver: NetworkDriver = None):
        # Default to SimulationDriver which safely runs in sandbox/CI environments
        # LinuxKernelDriver is used when real CAP_NET_ADMIN / sudo is configured
        self.driver = driver or SimulationDriver()

    def set_driver(self, driver: NetworkDriver):
        self.driver = driver

    def preview_deployment(self, topology: Topology) -> DeploymentPreview:
        """Pre-computes resources, validates safety constraints, and returns deployment preview."""
        namespaces = []
        bridges = []
        veth_pairs = []
        nftables_tables = []
        safety_passed = True

        for dev in topology.devices:
            ns_name = dev.namespace_name or f"cl-ns-{dev.name.lower().replace(' ', '-')}"
            try:
                HostProtectionValidator.validate_namespace_name(ns_name)
                namespaces.append(ns_name)
            except HostProtectionError:
                safety_passed = False

            if dev.device_type == "firewall":
                nftables_tables.append(f"cl_fw_{dev.name.lower().replace(' ', '_')}")

        for seg in topology.segments:
            try:
                HostProtectionValidator.validate_interface_name(seg.bridge_name)
                bridges.append(seg.bridge_name)
            except HostProtectionError:
                safety_passed = False

        for conn in topology.connections:
            ep = conn.veth_name or f"cl-ep-{conn.id[:6]}"
            peer = conn.peer_name or f"cl-brp-{conn.id[:6]}"
            try:
                HostProtectionValidator.validate_interface_name(ep)
                HostProtectionValidator.validate_interface_name(peer)
                veth_pairs.append({"endpoint": ep, "peer": peer})
            except HostProtectionError:
                safety_passed = False

        return DeploymentPreview(
            topology_id=topology.id,
            topology_name=topology.name,
            namespaces_to_create=namespaces,
            bridges_to_create=bridges,
            veth_pairs_to_create=veth_pairs,
            nftables_tables_to_create=nftables_tables,
            safety_check_passed=safety_passed,
            protected_interfaces_safe=True,
            estimated_memory_kb=len(namespaces) * 2048 + len(bridges) * 1024
        )

    def deploy_topology(self, db: Session, topology_id: str, username: str) -> DeploymentResult:
        """Executes full deployment of all topology network resources."""
        topology = db.query(Topology).filter(Topology.id == topology_id).first()
        if not topology:
            raise ValueError(f"Topology {topology_id} not found.")

        # 1. Generate & validate preview
        preview = self.preview_deployment(topology)
        if not preview.safety_check_passed:
            raise HostProtectionError("Deployment aborted: One or more resources violate host safety rules.")

        created_summary = {"bridges": [], "namespaces": [], "veths": [], "routes": []}

        try:
            # 2. Create Bridges (Network Segments)
            for seg in topology.segments:
                self.driver.create_bridge(seg.bridge_name, vlan_filtering=bool(seg.vlan_id))
                seg.status = "ACTIVE"
                created_summary["bridges"].append(seg.bridge_name)

            # 3. Create Namespaces (Devices)
            for dev in topology.devices:
                ns_name = dev.namespace_name or f"cl-ns-{dev.name.lower().replace(' ', '-')}"
                dev.namespace_name = ns_name
                self.driver.create_namespace(ns_name)
                dev.status = "RUNNING"
                created_summary["namespaces"].append(ns_name)

            # 4. Connect Veth Pairs (Links)
            for conn in topology.connections:
                src_dev = conn.source_device
                target_seg = conn.segment

                if src_dev and target_seg:
                    ep_name = conn.veth_name or f"cl-ep-{conn.id[:6]}"
                    brp_name = conn.peer_name or f"cl-brp-{conn.id[:6]}"
                    conn.veth_name = ep_name
                    conn.peer_name = brp_name

                    self.driver.create_veth_pair(
                        endpoint_iface=ep_name,
                        peer_iface=brp_name,
                        namespace=src_dev.namespace_name,
                        bridge_name=target_seg.bridge_name,
                        ip_cidr=f"{src_dev.ip_address}/24" if src_dev.ip_address else None,
                        vlan_id=target_seg.vlan_id
                    )
                    conn.status = "CONNECTED"
                    created_summary["veths"].append(f"{ep_name} <-> {brp_name}")

            # 5. Configure Gateway Routes for Devices
            for seg in topology.segments:
                if seg.gateway_ip:
                    for conn in seg.connections:
                        dev = conn.source_device
                        if dev and dev.ip_address and dev.ip_address != seg.gateway_ip:
                            self.driver.configure_route(dev.namespace_name, "default", seg.gateway_ip)
                            created_summary["routes"].append(f"{dev.name} -> {seg.gateway_ip}")

            # Update Topology Status
            topology.status = "DEPLOYED"

            # Log to Immutable Audit Trail
            audit = AuditLog(
                username=username,
                action="TOPOLOGY_DEPLOYED",
                resource_type="network_topology",
                resource_id=topology.id,
                status="SUCCESS",
                details=f"Deployed topology '{topology.name}' ({len(created_summary['namespaces'])} namespaces, {len(created_summary['bridges'])} bridges)"
            )
            db.add(audit)
            db.commit()

            return DeploymentResult(
                topology_id=topology.id,
                status="DEPLOYED",
                details=created_summary,
                message=f"Successfully deployed topology '{topology.name}'"
            )

        except Exception as e:
            logger.error(f"Error deploying topology {topology_id}: {e}", exc_info=True)
            db.rollback()
            # Attempt rollback of partially created resources
            self.teardown_topology(db, topology_id, username)
            raise

    def teardown_topology(self, db: Session, topology_id: str, username: str) -> DeploymentResult:
        """Safely cleans up all kernel and simulated resources belonging to a topology."""
        topology = db.query(Topology).filter(Topology.id == topology_id).first()
        if not topology:
            raise ValueError(f"Topology {topology_id} not found.")

        deleted_summary = {"veths": [], "bridges": [], "namespaces": []}

        # 1. Delete Veth Pairs
        for conn in topology.connections:
            if conn.veth_name:
                self.driver.delete_veth_pair(conn.veth_name)
                deleted_summary["veths"].append(conn.veth_name)
            conn.status = "DISCONNECTED"

        # 2. Delete Bridges
        for seg in topology.segments:
            if seg.bridge_name:
                self.driver.delete_bridge(seg.bridge_name)
                deleted_summary["bridges"].append(seg.bridge_name)
            seg.status = "INACTIVE"

        # 3. Delete Namespaces
        for dev in topology.devices:
            if dev.namespace_name:
                self.driver.delete_namespace(dev.namespace_name)
                deleted_summary["namespaces"].append(dev.namespace_name)
            dev.status = "STOPPED"

        topology.status = "STOPPED"

        audit = AuditLog(
            username=username,
            action="TOPOLOGY_TEARDOWN",
            resource_type="network_topology",
            resource_id=topology.id,
            status="SUCCESS",
            details=f"Cleaned up topology '{topology.name}' resources."
        )
        db.add(audit)
        db.commit()

        return DeploymentResult(
            topology_id=topology.id,
            status="STOPPED",
            details=deleted_summary,
            message=f"Successfully teared down topology '{topology.name}'"
        )


network_manager = NetworkEngineManager()
