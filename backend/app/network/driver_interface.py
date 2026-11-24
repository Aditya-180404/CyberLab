"""
Network Engine Driver Interface
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class NetworkDriver(ABC):
    @abstractmethod
    def create_namespace(self, netns_name: str) -> bool:
        pass

    @abstractmethod
    def delete_namespace(self, netns_name: str) -> bool:
        pass

    @abstractmethod
    def create_bridge(self, bridge_name: str, vlan_filtering: bool = True) -> bool:
        pass

    @abstractmethod
    def delete_bridge(self, bridge_name: str) -> bool:
        pass

    @abstractmethod
    def create_veth_pair(
        self,
        endpoint_iface: str,
        peer_iface: str,
        namespace: str,
        bridge_name: str,
        ip_cidr: Optional[str] = None,
        vlan_id: Optional[int] = None
    ) -> bool:
        pass

    @abstractmethod
    def delete_veth_pair(self, endpoint_iface: str) -> bool:
        pass

    @abstractmethod
    def configure_route(self, namespace: str, dest_cidr: str, gateway_ip: str) -> bool:
        pass

    @abstractmethod
    def apply_nftables(self, namespace: str, table_name: str, rules: List[str]) -> bool:
        pass

    @abstractmethod
    def inspect_resource_state(self, resource_name: str) -> Dict[str, Any]:
        pass
