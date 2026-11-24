"""
Unified Asset Inventory Engine (Phase 5)
Synchronizes, deduplicates, and calculates dynamic risk scores across all platform assets:
VMware Virtual Machines, Distributed Agents, and Simulated Network Nodes.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.asset import Asset, AssetType, AssetCriticality, AssetStatus
from app.models.vm import VirtualMachine, PowerState
from app.models.agent import Agent, AgentStatus, AgentTelemetry
from app.models.device import NetworkDevice

logger = logging.getLogger("cyberlab.inventory")


class AssetManager:
    """Orchestrates asset discovery, entity deduplication, and dynamic security risk scoring."""

    def calculate_risk_score(
        self,
        is_vulnerable: bool = False,
        is_bridged: bool = False,
        is_running: bool = False,
        fim_alerts_count: int = 0,
        listening_ports: Optional[List[int]] = None,
        agent_status: Optional[str] = None
    ) -> int:
        """Calculates normalized asset security risk score (0 - 100)."""
        score = 10  # Baseline exposure

        # 1. Known vulnerable target weighting (Metasploitable, VulnHub)
        if is_vulnerable:
            score += 55

        # 2. Dangerous network exposure (bridged to physical LAN)
        if is_bridged:
            score += 25

        # 3. Active execution exposure
        if is_running:
            score += 5

        # 4. Integrity violations detected by EDR agent
        if fim_alerts_count > 0:
            score += min(fim_alerts_count * 15, 30)

        # 5. Sensitive/unencrypted legacy listening services
        if listening_ports:
            for p in listening_ports:
                if p in [21, 23, 80, 110, 143]:  # FTP, Telnet, HTTP, POP3, IMAP
                    score += 10
                elif p < 1024:
                    score += 3

        # 6. Containment / Credential states
        if agent_status == AgentStatus.ISOLATED:
            score += 15
        elif agent_status == AgentStatus.REVOKED:
            score += 25

        return min(max(score, 0), 100)

    def sync_all(self, db: Session) -> Dict[str, Any]:
        """Synchronizes and reconciles all registered entities into unified Asset records."""
        vm_count = 0
        agent_count = 0
        sim_count = 0

        # -------------------------------------------------------------
        # 1. Sync Virtual Machines
        # -------------------------------------------------------------
        vms = db.query(VirtualMachine).all()
        for vm in vms:
            adapters = json.loads(vm.network_adapters_json or "[]")
            ips = []
            macs = [a.get("mac_address") for a in adapters if a.get("mac_address")]
            is_bridged = any(a.get("is_bridged", False) for a in adapters)

            # Check if asset exists for this VM
            asset = db.query(Asset).filter(
                (Asset.virtual_machine_id == vm.id) | (Asset.name == vm.name)
            ).first()

            sec_tags = []
            if vm.is_vulnerable_target:
                sec_tags.append("VULNERABLE_TARGET")
            if is_bridged:
                sec_tags.append("BRIDGED_ADAPTER")
            if vm.power_state == PowerState.RUNNING:
                sec_tags.append("RUNNING_VM")

            risk = self.calculate_risk_score(
                is_vulnerable=vm.is_vulnerable_target,
                is_bridged=is_bridged,
                is_running=(vm.power_state == PowerState.RUNNING)
            )

            criticality = AssetCriticality.HIGH if vm.is_vulnerable_target else AssetCriticality.MEDIUM
            exposure = "PUBLIC" if is_bridged else "ISOLATED" if vm.is_vulnerable_target else "INTERNAL"

            specs = {"vcpus": vm.vcpus, "memory_mb": vm.memory_mb, "hypervisor": vm.hypervisor_type}

            if not asset:
                asset = Asset(
                    organization_id=vm.organization_id,
                    name=vm.name,
                    asset_type=AssetType.VIRTUAL_MACHINE,
                    ip_addresses_json=json.dumps(ips),
                    mac_addresses_json=json.dumps(macs),
                    os_family="Linux" if "linux" in vm.os_type.lower() or "ubuntu" in vm.os_type.lower() else "Windows",
                    os_version=vm.os_type,
                    criticality=criticality,
                    risk_score=risk,
                    exposure=exposure,
                    status=AssetStatus.ACTIVE,
                    virtual_machine_id=vm.id,
                    hardware_specs_json=json.dumps(specs),
                    security_tags_json=json.dumps(sec_tags),
                    last_seen=datetime.now(timezone.utc)
                )
                db.add(asset)
            else:
                asset.virtual_machine_id = vm.id
                asset.name = vm.name
                asset.os_version = vm.os_type
                asset.mac_addresses_json = json.dumps(macs)
                asset.hardware_specs_json = json.dumps(specs)
                asset.risk_score = risk
                asset.security_tags_json = json.dumps(list(set(json.loads(asset.security_tags_json or "[]") + sec_tags)))
                asset.last_seen = datetime.now(timezone.utc)

            vm_count += 1

        db.flush()

        # -------------------------------------------------------------
        # 2. Sync Distributed Linux Agents
        # -------------------------------------------------------------
        agents = db.query(Agent).all()
        for agent in agents:
            # Check for existing asset by agent_id or hostname or IP
            asset = db.query(Asset).filter(
                (Asset.agent_id == agent.id) | (Asset.name == agent.hostname)
            ).first()

            # Analyze latest telemetry
            latest_tel = agent.telemetry[0] if agent.telemetry else None
            services = []
            listening_ports = []
            fim_count = 0
            if latest_tel:
                sockets = json.loads(latest_tel.network_connections_json or "[]")
                for s in sockets:
                    port = s.get("local_port") or (int(s.get("local").split(":")[-1]) if ":" in s.get("local", "") else None)
                    if port:
                        listening_ports.append(port)
                        services.append({
                            "port": port,
                            "protocol": s.get("protocol", "tcp").lower(),
                            "state": s.get("state") or s.get("status") or "LISTEN"
                        })
                fim_alerts = json.loads(latest_tel.fim_alerts_json or "[]")
                fim_count = len(fim_alerts)

            risk = self.calculate_risk_score(
                fim_alerts_count=fim_count,
                listening_ports=listening_ports,
                agent_status=agent.status
            )

            specs = json.loads(agent.hardware_specs_json or "{}")
            sec_tags = ["EDR_MONITORED"]
            if fim_count > 0:
                sec_tags.append("FIM_ALERT_ACTIVE")
            if agent.status == AgentStatus.ISOLATED:
                sec_tags.append("QUARANTINED")

            ips = [agent.ip_address] if agent.ip_address else []

            if not asset:
                asset = Asset(
                    organization_id=agent.organization_id,
                    site_id=agent.site_id,
                    name=agent.hostname,
                    asset_type=AssetType.AGENT_HOST,
                    ip_addresses_json=json.dumps(ips),
                    os_family=agent.os_type,
                    os_version=agent.os_release,
                    kernel_version=agent.kernel_version,
                    criticality=AssetCriticality.HIGH if fim_count > 0 else AssetCriticality.MEDIUM,
                    risk_score=risk,
                    exposure="INTERNAL",
                    status=AssetStatus.QUARANTINED if agent.status == AgentStatus.ISOLATED else AssetStatus.ACTIVE,
                    agent_id=agent.id,
                    hardware_specs_json=json.dumps(specs),
                    services_json=json.dumps(services),
                    security_tags_json=json.dumps(sec_tags),
                    last_seen=agent.last_heartbeat or datetime.now(timezone.utc)
                )
                db.add(asset)
            else:
                asset.agent_id = agent.id
                asset.kernel_version = agent.kernel_version
                asset.services_json = json.dumps(services)
                # Keep higher risk if multiple factors exist
                asset.risk_score = max(asset.risk_score, risk)
                current_tags = json.loads(asset.security_tags_json or "[]")
                asset.security_tags_json = json.dumps(list(set(current_tags + sec_tags)))
                asset.last_seen = agent.last_heartbeat or datetime.now(timezone.utc)
                if agent.status == AgentStatus.ISOLATED:
                    asset.status = AssetStatus.QUARANTINED

            agent_count += 1

        db.flush()

        # -------------------------------------------------------------
        # 3. Sync Simulated Network Devices
        # -------------------------------------------------------------
        devices = db.query(NetworkDevice).all()
        for dev in devices:
            asset = db.query(Asset).filter(
                (Asset.network_device_id == dev.id) | ((Asset.name == dev.name) & (Asset.asset_type == AssetType.SIMULATED_DEVICE))
            ).first()

            ips = [dev.ip_address] if dev.ip_address else []
            macs = [dev.mac_address] if dev.mac_address else []

            sec_tags = ["SIMULATED_TOPOLOGY"]
            if dev.device_type == "firewall":
                sec_tags.append("SECURITY_GATEWAY")

            if not asset:
                asset = Asset(
                    organization_id="default-org",
                    name=dev.name,
                    asset_type=AssetType.SIMULATED_DEVICE,
                    ip_addresses_json=json.dumps(ips),
                    mac_addresses_json=json.dumps(macs),
                    os_family="NetworkOS" if dev.device_type in ["router", "switch", "firewall"] else "Linux",
                    os_version=f"CyberLab {dev.device_type.capitalize()} Node",
                    criticality=AssetCriticality.HIGH if dev.device_type == "firewall" else AssetCriticality.LOW,
                    risk_score=15,
                    exposure="INTERNAL",
                    status=AssetStatus.ACTIVE if dev.status == "RUNNING" else AssetStatus.INACTIVE,
                    network_device_id=dev.id,
                    security_tags_json=json.dumps(sec_tags),
                    last_seen=datetime.now(timezone.utc)
                )
                db.add(asset)
            else:
                asset.network_device_id = dev.id
                asset.status = AssetStatus.ACTIVE if dev.status == "RUNNING" else AssetStatus.INACTIVE
                asset.last_seen = datetime.now(timezone.utc)

            sim_count += 1

        db.commit()

        total = vm_count + agent_count + sim_count
        logger.info(f"Asset synchronization complete. Total entities indexed: {total}")
        return {
            "total_synced": total,
            "vm_assets_synced": vm_count,
            "agent_assets_synced": agent_count,
            "simulated_assets_synced": sim_count,
            "message": f"Successfully synchronized {total} enterprise assets across all platform engines."
        }

    def get_kpis(self, db: Session) -> Dict[str, Any]:
        """Calculates fleet-wide asset statistics and risk indicators."""
        assets = db.query(Asset).all()
        total = len(assets)
        if total == 0:
            return {
                "total_assets": 0,
                "average_risk_score": 0.0,
                "high_risk_count": 0,
                "critical_assets_count": 0,
                "by_type": {},
                "by_criticality": {}
            }

        avg_risk = sum(a.risk_score for a in assets) / total
        high_risk = sum(1 for a in assets if a.risk_score >= 60)
        critical_count = sum(1 for a in assets if a.criticality == AssetCriticality.CRITICAL)

        by_type: Dict[str, int] = {}
        for a in assets:
            by_type[a.asset_type] = by_type.get(a.asset_type, 0) + 1

        by_crit: Dict[str, int] = {}
        for a in assets:
            by_crit[a.criticality] = by_crit.get(a.criticality, 0) + 1

        return {
            "total_assets": total,
            "average_risk_score": round(avg_risk, 1),
            "high_risk_count": high_risk,
            "critical_assets_count": critical_count,
            "by_type": by_type,
            "by_criticality": by_crit
        }


asset_manager = AssetManager()
