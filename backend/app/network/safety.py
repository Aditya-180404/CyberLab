"""
Host Protection & Safety Validator
Ensures CyberLab operations NEVER modify host physical interfaces, Wi-Fi, or default route.
"""
import re
from typing import List


class HostProtectionError(Exception):
    """Raised when an operation attempts to mutate protected host networking resources."""
    pass


class HostProtectionValidator:
    # Explicitly protected host interfaces (regex patterns)
    PROTECTED_PATTERNS: List[str] = [
        r"^lo$",
        r"^wlan\d*",
        r"^wlp\w+",
        r"^eth\d*",
        r"^enp\w+",
        r"^ens\w+",
        r"^docker\d*",
        r"^virbr\d*",
    ]

    # Required prefix for all CyberLab managed resources
    ALLOWED_PREFIXES: List[str] = [
        "cl-",
        "cl_",
    ]

    @classmethod
    def validate_interface_name(cls, iface_name: str) -> None:
        """Validates that the target interface is a CyberLab resource and not a host interface."""
        if not iface_name:
            raise HostProtectionError("Interface name cannot be empty.")

        # 1. Reject if matching protected host patterns
        for pattern in cls.PROTECTED_PATTERNS:
            if re.match(pattern, iface_name, re.IGNORECASE):
                raise HostProtectionError(
                    f"CRITICAL SAFETY VIOLATION: Operation on protected host interface '{iface_name}' is blocked."
                )

        # 2. Must adhere to CyberLab naming convention
        if not any(iface_name.startswith(prefix) for prefix in cls.ALLOWED_PREFIXES):
            raise HostProtectionError(
                f"SAFETY POLICY ENFORCEMENT: Interface '{iface_name}' must start with one of: {cls.ALLOWED_PREFIXES}"
            )

    @classmethod
    def validate_namespace_name(cls, netns_name: str) -> None:
        """Ensures namespace adheres to cl-ns-* convention."""
        if not netns_name or not (netns_name.startswith("cl-ns-") or netns_name.startswith("cl-")):
            raise HostProtectionError(
                f"Namespace '{netns_name}' must use the 'cl-ns-' prefix to ensure isolation from host."
            )

    @classmethod
    def validate_route(cls, dest_cidr: str, gateway_ip: str) -> None:
        """Prevents hijacking or altering the host default route (0.0.0.0/0)."""
        if dest_cidr in ["0.0.0.0/0", "default"] and not gateway_ip.startswith("10.") and not gateway_ip.startswith("172.") and not gateway_ip.startswith("192.168."):
            raise HostProtectionError(
                "SAFETY CHECK: Default route modification must use private RFC 1918 gateway inside simulated namespace."
            )
