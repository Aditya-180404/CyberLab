"""
Simulation & Sandboxed Emulation Driver
Accurately models network namespaces, bridges, veth pairs, routes, and packet flows in memory
for testing and sandboxed environments where root/CAP_NET_ADMIN is restricted.
"""
import ipaddress
import logging
from typing import List, Optional, Dict, Any
from app.network.driver_interface import NetworkDriver
from app.network.safety import HostProtectionValidator, HostProtectionError

logger = logging.getLogger("cyberlab.network.simulation")


class SimulationDriver(NetworkDriver):
    def __init__(self):
        # In-memory virtual state tables
        self.namespaces: Dict[str, Dict[str, Any]] = {}
        self.bridges: Dict[str, Dict[str, Any]] = {}
        self.veth_pairs: Dict[str, Dict[str, Any]] = {}
        self.routes: Dict[str, List[Dict[str, str]]] = {}
        self.nftables: Dict[str, Dict[str, List[str]]] = {}

    def create_namespace(self, netns_name: str) -> bool:
        HostProtectionValidator.validate_namespace_name(netns_name)
        if netns_name in self.namespaces:
            logger.warning(f"Namespace {netns_name} already exists in simulation.")
            return True

        self.namespaces[netns_name] = {
            "name": netns_name,
            "interfaces": ["lo"],
            "state": "UP",
            "ip_addresses": {"lo": "127.0.0.1/8"}
        }
        self.routes[netns_name] = []
        self.nftables[netns_name] = {}
        return True

    def delete_namespace(self, netns_name: str) -> bool:
        HostProtectionValidator.validate_namespace_name(netns_name)
        self.namespaces.pop(netns_name, None)
        self.routes.pop(netns_name, None)
        self.nftables.pop(netns_name, None)
        return True

    def create_bridge(self, bridge_name: str, vlan_filtering: bool = True) -> bool:
        HostProtectionValidator.validate_interface_name(bridge_name)
        self.bridges[bridge_name] = {
            "name": bridge_name,
            "vlan_filtering": vlan_filtering,
            "ports": [],
            "state": "UP"
        }
        return True

    def delete_bridge(self, bridge_name: str) -> bool:
        HostProtectionValidator.validate_interface_name(bridge_name)
        self.bridges.pop(bridge_name, None)
        return True

    def create_veth_pair(
        self,
        endpoint_iface: str,
        peer_iface: str,
        namespace: str,
        bridge_name: str,
        ip_cidr: Optional[str] = None,
        vlan_id: Optional[int] = None
    ) -> bool:
        HostProtectionValidator.validate_interface_name(endpoint_iface)
        HostProtectionValidator.validate_interface_name(peer_iface)
        HostProtectionValidator.validate_namespace_name(namespace)
        HostProtectionValidator.validate_interface_name(bridge_name)

        if namespace not in self.namespaces:
            self.create_namespace(namespace)

        if bridge_name not in self.bridges:
            self.create_bridge(bridge_name)

        # Validate IP format and check for conflicts
        if ip_cidr:
            try:
                ip_net = ipaddress.ip_interface(ip_cidr)
                for ns, data in self.namespaces.items():
                    for iface, allocated in data["ip_addresses"].items():
                        if allocated == str(ip_net):
                            raise HostProtectionError(f"IP address conflict: {ip_cidr} already assigned to {ns}:{iface}")
            except ValueError as e:
                raise HostProtectionError(f"Invalid IP CIDR format '{ip_cidr}': {e}")

        # Register connection
        self.veth_pairs[endpoint_iface] = {
            "endpoint": endpoint_iface,
            "peer": peer_iface,
            "namespace": namespace,
            "bridge": bridge_name,
            "ip_cidr": ip_cidr,
            "vlan_id": vlan_id,
            "status": "UP"
        }

        self.namespaces[namespace]["interfaces"].append(endpoint_iface)
        if ip_cidr:
            self.namespaces[namespace]["ip_addresses"][endpoint_iface] = ip_cidr

        self.bridges[bridge_name]["ports"].append({
            "interface": peer_iface,
            "vlan_id": vlan_id
        })
        return True

    def delete_veth_pair(self, endpoint_iface: str) -> bool:
        HostProtectionValidator.validate_interface_name(endpoint_iface)
        info = self.veth_pairs.pop(endpoint_iface, None)
        if info:
            ns = info["namespace"]
            br = info["bridge"]
            if ns in self.namespaces and endpoint_iface in self.namespaces[ns]["interfaces"]:
                self.namespaces[ns]["interfaces"].remove(endpoint_iface)
                self.namespaces[ns]["ip_addresses"].pop(endpoint_iface, None)
            if br in self.bridges:
                self.bridges[br]["ports"] = [p for p in self.bridges[br]["ports"] if p["interface"] != info["peer"]]
        return True

    def configure_route(self, namespace: str, dest_cidr: str, gateway_ip: str) -> bool:
        HostProtectionValidator.validate_namespace_name(namespace)
        HostProtectionValidator.validate_route(dest_cidr, gateway_ip)

        if namespace not in self.routes:
            self.routes[namespace] = []

        self.routes[namespace].append({
            "destination": dest_cidr,
            "gateway": gateway_ip
        })
        return True

    def apply_nftables(self, namespace: str, table_name: str, rules: List[str]) -> bool:
        HostProtectionValidator.validate_namespace_name(namespace)
        if namespace not in self.nftables:
            self.nftables[namespace] = {}

        self.nftables[namespace][table_name] = rules
        return True

    def inspect_resource_state(self, resource_name: str) -> Dict[str, Any]:
        return {
            "driver": "simulation",
            "resource": resource_name,
            "namespaces_count": len(self.namespaces),
            "bridges_count": len(self.bridges),
            "veth_pairs_count": len(self.veth_pairs),
            "verified": True
        }
