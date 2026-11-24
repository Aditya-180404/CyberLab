"""
VMware VMX Configuration File Parser & Safety Inspector
Safely parses VMware configuration keys without executing or modifying the file.
"""
import os
import re
from typing import Dict, Any, List


class VMXParser:
    @staticmethod
    def parse_vmx(file_path: str) -> Dict[str, Any]:
        """Parses a .vmx file into key-value pairs."""
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"VMX file not found: {file_path}")

        config = {}
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip().lower()
                    val = val.strip().strip('"')
                    config[key] = val

        # Extract Core Hardware Specs
        display_name = config.get("displayname") or os.path.basename(os.path.dirname(file_path)) or os.path.splitext(os.path.basename(file_path))[0]
        memsize = int(config.get("memsize", "1024"))
        vcpus = int(config.get("numvcpus", "1"))
        os_type = config.get("guestos", "Linux")

        # Extract Network Adapters
        adapters: List[Dict[str, Any]] = []
        for i in range(10):
            prefix = f"ethernet{i}"
            if f"{prefix}.present" in config and config[f"{prefix}.present"].lower() == "true":
                conn_type = config.get(f"{prefix}.connectiontype", "custom").lower()
                vnet = config.get(f"{prefix}.vnet", "vmnet1")
                mac = config.get(f"{prefix}.generatedaddress") or config.get(f"{prefix}.address")
                vdev = config.get(f"{prefix}.virtualdev", "e1000")
                is_bridged = conn_type in ["bridged", "bridge"]

                adapters.append({
                    "name": prefix,
                    "connection_type": conn_type,
                    "vnet": vnet,
                    "mac_address": mac,
                    "virtual_dev": vdev,
                    "is_bridged": is_bridged
                })

        # Check Vulnerable Target Keywords
        lower_name = display_name.lower()
        lower_path = file_path.lower()
        is_vulnerable = any(
            v in lower_name or v in lower_path
            for v in ["metasploit", "stapler", "kioptrix", "vulnhub", "dvwa", "hackthebox", "badstore"]
        )

        # Safety Check: Vulnerable system on Bridged mode
        safety_warning = None
        has_bridged = any(a["is_bridged"] for a in adapters)
        if is_vulnerable and has_bridged:
            safety_warning = (
                "CRITICAL SECURITY RISK: Vulnerable target VM is configured in BRIDGED mode. "
                "It is exposed to the local physical Wi-Fi/LAN! Immediately switch to Host-Only (vmnet1)."
            )

        return {
            "name": display_name,
            "memory_mb": memsize,
            "vcpus": vcpus,
            "os_type": os_type,
            "network_adapters": adapters,
            "is_vulnerable_target": is_vulnerable,
            "safety_warning": safety_warning
        }
