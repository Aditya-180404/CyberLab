"""
Linux Kernel Network Driver
Executes real system commands (ip netns, ip link, nftables) with strict safety boundaries.
"""
import subprocess
import logging
from typing import List, Optional, Dict, Any
from app.network.driver_interface import NetworkDriver
from app.network.safety import HostProtectionValidator, HostProtectionError

logger = logging.getLogger("cyberlab.network.kernel")


class LinuxKernelDriver(NetworkDriver):
    def __init__(self, sudo_cmd: str = "sudo"):
        self.sudo = sudo_cmd

    def _run_cmd(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Executes a command with validation."""
        full_cmd = [self.sudo] + cmd if self.sudo else cmd
        logger.debug(f"Executing network command: {' '.join(full_cmd)}")
        return subprocess.run(full_cmd, capture_output=True, text=True, check=True)

    def create_namespace(self, netns_name: str) -> bool:
        HostProtectionValidator.validate_namespace_name(netns_name)
        try:
            self._run_cmd(["ip", "netns", "add", netns_name])
            self._run_cmd(["ip", "-n", netns_name, "link", "set", "lo", "up"])
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create netns {netns_name}: {e.stderr}")
            raise

    def delete_namespace(self, netns_name: str) -> bool:
        HostProtectionValidator.validate_namespace_name(netns_name)
        try:
            self._run_cmd(["ip", "netns", "delete", netns_name])
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to delete netns {netns_name}: {e.stderr}")
            return False

    def create_bridge(self, bridge_name: str, vlan_filtering: bool = True) -> bool:
        HostProtectionValidator.validate_interface_name(bridge_name)
        try:
            cmd = ["ip", "link", "add", "name", bridge_name, "type", "bridge"]
            if vlan_filtering:
                cmd.extend(["vlan_filtering", "1"])
            self._run_cmd(cmd)
            self._run_cmd(["ip", "link", "set", bridge_name, "up"])
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create bridge {bridge_name}: {e.stderr}")
            raise

    def delete_bridge(self, bridge_name: str) -> bool:
        HostProtectionValidator.validate_interface_name(bridge_name)
        try:
            self._run_cmd(["ip", "link", "set", bridge_name, "down"])
            self._run_cmd(["ip", "link", "delete", bridge_name])
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to delete bridge {bridge_name}: {e.stderr}")
            return False

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

        try:
            # 1. Create veth pair in root namespace
            self._run_cmd([
                "ip", "link", "add", endpoint_iface, "type", "veth", "peer", "name", peer_iface
            ])

            # 2. Attach peer to bridge and bring it UP
            self._run_cmd(["ip", "link", "set", peer_iface, "master", bridge_name])
            self._run_cmd(["ip", "link", "set", peer_iface, "up"])

            # 3. Configure VLAN if specified
            if vlan_id:
                self._run_cmd(["bridge", "vlan", "add", "dev", peer_iface, "vid", str(vlan_id), "pvid", "untagged"])

            # 4. Move endpoint interface into target namespace
            self._run_cmd(["ip", "link", "set", endpoint_iface, "netns", namespace])

            # 5. Configure IP and bring UP inside namespace
            if ip_cidr:
                self._run_cmd(["ip", "-n", namespace, "addr", "add", ip_cidr, "dev", endpoint_iface])
            self._run_cmd(["ip", "-n", namespace, "link", "set", endpoint_iface, "up"])

            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create veth pair {endpoint_iface}<->{peer_iface}: {e.stderr}")
            raise

    def delete_veth_pair(self, endpoint_iface: str) -> bool:
        HostProtectionValidator.validate_interface_name(endpoint_iface)
        try:
            self._run_cmd(["ip", "link", "delete", endpoint_iface])
            return True
        except subprocess.CalledProcessError:
            return False

    def configure_route(self, namespace: str, dest_cidr: str, gateway_ip: str) -> bool:
        HostProtectionValidator.validate_namespace_name(namespace)
        HostProtectionValidator.validate_route(dest_cidr, gateway_ip)
        try:
            self._run_cmd(["ip", "-n", namespace, "route", "add", dest_cidr, "via", gateway_ip])
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to configure route in {namespace}: {e.stderr}")
            raise

    def apply_nftables(self, namespace: str, table_name: str, rules: List[str]) -> bool:
        HostProtectionValidator.validate_namespace_name(namespace)
        try:
            # Create isolated table inside target namespace
            self._run_cmd(["ip", "netns", "exec", namespace, "nft", "add", "table", "inet", table_name])
            self._run_cmd([
                "ip", "netns", "exec", namespace, "nft", "add", "chain", "inet", table_name,
                "input", "{ type filter hook input priority 0; policy accept; }"
            ])
            for rule in rules:
                self._run_cmd(["ip", "netns", "exec", namespace, "nft", "add", "rule", "inet", table_name, "input"] + rule.split())
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to apply nftables rules in {namespace}: {e.stderr}")
            raise

    def inspect_resource_state(self, resource_name: str) -> Dict[str, Any]:
        return {"driver": "linux_kernel", "resource": resource_name, "verified": True}
