"""
Digital Twin & Attack-Path Analysis Engine (Phase 8)
Builds topological models using NetworkX, computes reachability,
evaluates blast radius, discovers attack paths, and identifies defensive choke points.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set, Tuple
import networkx as nx
from sqlalchemy.orm import Session

from app.models.asset import Asset, AssetCriticality, AssetStatus, AssetType
from app.models.topology import Topology
from app.models.device import NetworkDevice, DeviceType
from app.models.segment import NetworkSegment
from app.models.connection import NetworkConnection
from app.models.vm import VirtualMachine
from app.models.siem import SecurityIncident, SecurityAlert, IncidentStatus, AlertStatus, EventSeverity
from app.schemas.digital_twin import (
    DigitalTwinNode, DigitalTwinEdge, DigitalTwinGraphResponse, DigitalTwinGraphSummary,
    DigitalTwinNodeType, AttackPathRequest, AttackPathResponse, AttackPathItem, AttackPathStep,
    BlastRadiusResponse, ReachableAssetDetail, ChokePointResponse, ChokePointItem
)

# Global set to store transient simulated compromises for what-if scenarios
_TRANSIENT_COMPROMISES: Set[str] = set()


class DigitalTwinGraphEngine:
    def __init__(self, db: Session, organization_id: str):
        self.db = db
        self.organization_id = organization_id
        self.graph = nx.DiGraph()
        self.nodes_dict: Dict[str, DigitalTwinNode] = {}
        self.edges_dict: Dict[str, DigitalTwinEdge] = {}
        self._build_graph()

    @classmethod
    def set_simulated_compromise(cls, node_id: str, compromised: bool = True):
        if compromised:
            _TRANSIENT_COMPROMISES.add(node_id)
        else:
            _TRANSIENT_COMPROMISES.discard(node_id)

    @classmethod
    def clear_simulated_compromises(cls):
        _TRANSIENT_COMPROMISES.clear()

    def _determine_zone(self, node_id: str, label: str, ip: str, exposure: str) -> str:
        label_lower = label.lower()
        if "adversary" in label_lower or "attacker" in label_lower or "kali" in label_lower or "wan" in label_lower or exposure == "PUBLIC":
            return "EXTERNAL"
        if "dmz" in label_lower or "web" in label_lower or "proxy" in label_lower:
            return "DMZ"
        if "vault" in label_lower or "db" in label_lower or "crown" in label_lower or "database" in label_lower or "secret" in label_lower:
            return "SECURE_VAULT"
        if "fw" in label_lower or "firewall" in label_lower or "router" in label_lower or "gateway" in label_lower:
            return "TRANSIT_ROUTER"
        return "INTERNAL"

    def _build_graph(self):
        """Construct the directed graph from database assets, topologies, and synthetic fallback nodes."""
        self.graph.clear()
        self.nodes_dict.clear()
        self.edges_dict.clear()

        # 1. Fetch active incidents / alerts to detect compromised state
        active_incidents = self.db.query(SecurityIncident).filter(
            SecurityIncident.organization_id == self.organization_id,
            SecurityIncident.status.in_([IncidentStatus.OPEN, IncidentStatus.ACTIVE])
        ).all()
        compromised_asset_ids = {inc.primary_asset_id for inc in active_incidents if inc.primary_asset_id}

        critical_alerts = self.db.query(SecurityAlert).filter(
            SecurityAlert.organization_id == self.organization_id,
            SecurityAlert.status.in_([AlertStatus.OPEN, AlertStatus.INVESTIGATING]),
            SecurityAlert.severity.in_([EventSeverity.HIGH, EventSeverity.CRITICAL])
        ).all()
        for alt in critical_alerts:
            if alt.asset_id:
                compromised_asset_ids.add(alt.asset_id)

        # Merge with transient what-if compromises
        compromised_asset_ids.update(_TRANSIENT_COMPROMISES)

        # 2. Ingest Assets from Inventory
        db_assets = self.db.query(Asset).filter(Asset.organization_id == self.organization_id).all()
        for asset in db_assets:
            ip_list = []
            if asset.ip_addresses_json:
                try:
                    ip_list = json.loads(asset.ip_addresses_json)
                except Exception:
                    ip_list = [asset.ip_addresses_json]
            
            services_list = []
            if asset.services_json:
                try:
                    services_list = json.loads(asset.services_json)
                except Exception:
                    pass

            tags = []
            if asset.security_tags_json:
                try:
                    tags = json.loads(asset.security_tags_json)
                except Exception:
                    pass

            is_comp = (asset.id in compromised_asset_ids) or ("VULNERABLE_TARGET" in tags and asset.id in _TRANSIENT_COMPROMISES)
            zone = self._determine_zone(asset.id, asset.name, ip_list[0] if ip_list else "", asset.exposure)

            node = DigitalTwinNode(
                id=asset.id,
                label=asset.name,
                node_type=DigitalTwinNodeType.ASSET,
                asset_type=asset.asset_type,
                ip_addresses=ip_list,
                zone=zone,
                criticality=asset.criticality,
                risk_score=min(100, asset.risk_score + (30 if is_comp else 0)),
                is_compromised=is_comp,
                status=asset.status,
                services=services_list,
                security_tags=tags,
                position=None
            )
            self.nodes_dict[node.id] = node
            self.graph.add_node(node.id, **node.model_dump())

        # 3. Ingest Simulated Devices and Segments if present
        devices = self.db.query(NetworkDevice).all()
        for dev in devices:
            if dev.id not in self.nodes_dict:
                node = DigitalTwinNode(
                    id=dev.id,
                    label=dev.name,
                    node_type=DigitalTwinNodeType.DEVICE,
                    device_type=dev.device_type,
                    ip_addresses=[dev.ip_address] if dev.ip_address else [],
                    zone="TRANSIT_ROUTER" if dev.device_type in [DeviceType.ROUTER, DeviceType.FIREWALL] else "INTERNAL",
                    criticality=AssetCriticality.HIGH if dev.device_type == DeviceType.FIREWALL else AssetCriticality.MEDIUM,
                    risk_score=20,
                    is_compromised=dev.id in compromised_asset_ids,
                    status=dev.status,
                    position=None
                )
                self.nodes_dict[node.id] = node
                self.graph.add_node(node.id, **node.model_dump())

        # Ingest Segments
        segments = self.db.query(NetworkSegment).all()
        for seg in segments:
            if seg.id not in self.nodes_dict:
                node = DigitalTwinNode(
                    id=seg.id,
                    label=f"Subnet {seg.name} ({seg.cidr_block})",
                    node_type=DigitalTwinNodeType.SEGMENT,
                    ip_addresses=[seg.gateway_ip] if seg.gateway_ip else [],
                    zone="DMZ" if "dmz" in seg.name.lower() else "INTERNAL",
                    criticality=AssetCriticality.LOW,
                    risk_score=10,
                    is_compromised=False,
                    status=seg.status,
                    position=None
                )
                self.nodes_dict[node.id] = node
                self.graph.add_node(node.id, **node.model_dump())

        # 4. Ingest Existing Topology Connections
        connections = self.db.query(NetworkConnection).all()
        for conn in connections:
            if conn.source_device_id in self.nodes_dict:
                target_id = conn.target_device_id or conn.segment_id
                if target_id and target_id in self.nodes_dict:
                    edge_id = f"edge-{conn.id[:8]}"
                    edge = DigitalTwinEdge(
                        id=edge_id,
                        source=conn.source_device_id,
                        target=target_id,
                        protocol="TCP",
                        ports=[22, 80, 443],
                        status="OPEN",
                        weight=1.0,
                        label=f"{conn.veth_name or 'link'}"
                    )
                    self.edges_dict[edge_id] = edge
                    self.graph.add_edge(edge.source, edge.target, **edge.model_dump())
                    # Bidirectional L2 connectivity
                    rev_id = f"edge-rev-{conn.id[:8]}"
                    self.graph.add_edge(edge.target, edge.source, id=rev_id, weight=1.0, protocol="TCP", ports=[22, 80, 443], status="OPEN")

        # 5. Seed Enterprise Digital Twin Topology (Zones & Infrastructure)
        # Ensure there is always a comprehensive, end-to-end path from External Attacker -> Perimeter FW -> DMZ -> Core Router -> Internal LAN -> Secure DB Vault
        self._ensure_enterprise_twin_topology(compromised_asset_ids)

        # 6. Apply realistic node coordinates for seamless React Flow layout
        self._assign_coordinates()

    def _ensure_enterprise_twin_topology(self, compromised_ids: Set[str]):
        """Injects essential architectural anchors so attack-path & blast-radius analysis have realistic targets."""
        anchors = [
            DigitalTwinNode(
                id="node-adversary-ext-01",
                label="Adversary Entrypoint (WAN/Internet)",
                node_type=DigitalTwinNodeType.ADVERSARY,
                ip_addresses=["198.51.100.50"],
                zone="EXTERNAL",
                criticality=AssetCriticality.LOW,
                risk_score=95,
                is_compromised=True,
                status="ACTIVE",
                security_tags=["THREAT_ACTOR", "EXTERNAL_INGRESS"]
            ),
            DigitalTwinNode(
                id="node-perimeter-fw-01",
                label="Perimeter Edge Firewall (nftables)",
                node_type=DigitalTwinNodeType.DEVICE,
                device_type="firewall",
                ip_addresses=["198.51.100.1", "10.10.10.1"],
                zone="TRANSIT_ROUTER",
                criticality=AssetCriticality.HIGH,
                risk_score=25,
                is_compromised="node-perimeter-fw-01" in compromised_ids,
                status="ACTIVE",
                security_tags=["EDGE_DEFENSE", "STATEFUL_FILTER"]
            ),
            DigitalTwinNode(
                id="node-dmz-web-proxy-01",
                label="DMZ Reverse Proxy & Web Gateway",
                node_type=DigitalTwinNodeType.ASSET,
                asset_type=AssetType.SIMULATED_DEVICE,
                ip_addresses=["10.10.10.15"],
                zone="DMZ",
                criticality=AssetCriticality.MEDIUM,
                risk_score=60,
                is_compromised="node-dmz-web-proxy-01" in compromised_ids,
                status="ACTIVE",
                services=[{"port": 80, "service": "http"}, {"port": 443, "service": "https"}],
                security_tags=["DMZ_EXPOSED", "NGINX"]
            ),
            DigitalTwinNode(
                id="node-core-router-01",
                label="Internal Core Transit Router (cl-core-rt)",
                node_type=DigitalTwinNodeType.DEVICE,
                device_type="router",
                ip_addresses=["10.10.10.254", "10.10.20.1", "10.10.30.1"],
                zone="TRANSIT_ROUTER",
                criticality=AssetCriticality.HIGH,
                risk_score=35,
                is_compromised="node-core-router-01" in compromised_ids,
                status="ACTIVE",
                security_tags=["TRANSIT_CHOKEPOINT", "VLAN_BRIDGE"]
            ),
            DigitalTwinNode(
                id="node-crown-jewel-db-vault",
                label="Crown Jewel: Enterprise Database Vault",
                node_type=DigitalTwinNodeType.ASSET,
                asset_type=AssetType.SIMULATED_DEVICE,
                ip_addresses=["10.10.30.50"],
                zone="SECURE_VAULT",
                criticality=AssetCriticality.CRITICAL,
                risk_score=15,
                is_compromised="node-crown-jewel-db-vault" in compromised_ids,
                status="ACTIVE",
                services=[{"port": 5432, "service": "postgresql"}, {"port": 3306, "service": "mysql"}],
                security_tags=["CROWN_JEWEL", "PII_SECRETS", "RESTRICTED_ACCESS"]
            ),
        ]

        for anchor in anchors:
            if anchor.id not in self.nodes_dict:
                self.nodes_dict[anchor.id] = anchor
                self.graph.add_node(anchor.id, **anchor.model_dump())
            else:
                # Update compromise status if dynamically set
                if anchor.id in compromised_ids:
                    self.nodes_dict[anchor.id].is_compromised = True
                    self.graph.nodes[anchor.id]["is_compromised"] = True

        # Backbone connections
        backbone_edges = [
            ("node-adversary-ext-01", "node-perimeter-fw-01", "TCP", [80, 443, 22], 1.2, "External Port Scan / Probe"),
            ("node-perimeter-fw-01", "node-dmz-web-proxy-01", "TCP", [80, 443], 0.8, "DMZ Ingress Forwarding"),
            ("node-dmz-web-proxy-01", "node-core-router-01", "TCP", [8080, 8443, 22], 2.0, "DMZ to Internal Routing"),
            ("node-core-router-01", "node-crown-jewel-db-vault", "TCP", [5432, 3306], 3.5, "Vault Restricted Transit"),
        ]

        for src, dst, proto, ports, weight, lbl in backbone_edges:
            eid = f"edge-{src[-6:]}-{dst[-6:]}"
            if not self.graph.has_edge(src, dst):
                edge = DigitalTwinEdge(id=eid, source=src, target=dst, protocol=proto, ports=ports, status="OPEN", weight=weight, label=lbl)
                self.edges_dict[eid] = edge
                self.graph.add_edge(src, dst, **edge.model_dump())

        # Link any discovered Assets/VMs (like Metasploitable2, Parrot, agent hosts) to the Core Router and LAN
        for nid, node in list(self.nodes_dict.items()):
            if node.zone == "INTERNAL" and node.node_type == DigitalTwinNodeType.ASSET and nid != "node-crown-jewel-db-vault":
                edge_to_core = f"edge-{nid[-6:]}-core"
                if not self.graph.has_edge("node-core-router-01", nid):
                    self.graph.add_edge("node-core-router-01", nid, id=f"edge-core-{nid[-6:]}", source="node-core-router-01", target=nid, protocol="TCP", ports=[22, 80], status="OPEN", weight=1.0, label="Internal LAN Link")
                if not self.graph.has_edge(nid, "node-core-router-01"):
                    self.graph.add_edge(nid, "node-core-router-01", id=edge_to_core, source=nid, target="node-core-router-01", protocol="TCP", ports=[22, 80], status="OPEN", weight=1.0, label="Internal LAN Uplink")
                # Direct route from internal asset to secure vault if vulnerable/compromised
                if node.is_compromised or "VULNERABLE_TARGET" in node.security_tags:
                    vault_link = f"edge-{nid[-6:]}-vault"
                    if not self.graph.has_edge(nid, "node-crown-jewel-db-vault"):
                        self.graph.add_edge(nid, "node-crown-jewel-db-vault", id=vault_link, source=nid, target="node-crown-jewel-db-vault", protocol="TCP", ports=[5432, 22], status="OPEN", weight=2.5, label="Lateral Pivot to DB Vault")

    def _assign_coordinates(self):
        """Assigns clean tiered coordinates (X, Y) for automated layout in React Flow."""
        zone_x = {
            "EXTERNAL": 60.0,
            "TRANSIT_ROUTER": 400.0,
            "DMZ": 380.0,
            "INTERNAL": 780.0,
            "SECURE_VAULT": 1180.0,
        }
        zone_counters: Dict[str, int] = {k: 0 for k in zone_x}

        # Specific custom overrides for key architectural nodes
        custom_pos = {
            "node-adversary-ext-01": (60.0, 260.0),
            "node-perimeter-fw-01": (280.0, 260.0),
            "node-dmz-web-proxy-01": (500.0, 150.0),
            "node-core-router-01": (720.0, 260.0),
            "node-crown-jewel-db-vault": (1200.0, 260.0),
        }

        for nid, node in self.nodes_dict.items():
            if nid in custom_pos:
                x, y = custom_pos[nid]
                node.position = {"x": x, "y": y}
                self.graph.nodes[nid]["position"] = node.position
            else:
                base_x = zone_x.get(node.zone, 780.0)
                idx = zone_counters.get(node.zone, 0)
                zone_counters[node.zone] = idx + 1
                y = 120.0 + (idx * 130.0)
                node.position = {"x": base_x, "y": y}
                self.graph.nodes[nid]["position"] = node.position

    def get_graph_data(self) -> DigitalTwinGraphResponse:
        """Returns the complete serialized graph with summary statistics."""
        nodes = list(self.nodes_dict.values())
        edges: List[DigitalTwinEdge] = []

        for u, v, data in self.graph.edges(data=True):
            edges.append(DigitalTwinEdge(
                id=data.get("id", f"edge-{u}-{v}"),
                source=u,
                target=v,
                protocol=data.get("protocol", "TCP"),
                ports=data.get("ports", [22]),
                status=data.get("status", "OPEN"),
                weight=float(data.get("weight", 1.0)),
                label=data.get("label", None)
            ))

        total_nodes = len(nodes)
        total_edges = len(edges)
        compromised_nodes = sum(1 for n in nodes if n.is_compromised)
        critical_nodes = sum(1 for n in nodes if n.criticality == AssetCriticality.CRITICAL)
        avg_risk = sum(n.risk_score for n in nodes) / max(1, total_nodes)

        # Choke points count: nodes with high betweenness centrality
        centrality = nx.betweenness_centrality(self.graph)
        choke_points_count = sum(1 for score in centrality.values() if score > 0.15)

        summary = DigitalTwinGraphSummary(
            total_nodes=total_nodes,
            total_edges=total_edges,
            compromised_nodes=compromised_nodes,
            critical_nodes=critical_nodes,
            average_risk_score=round(avg_risk, 1),
            choke_points_count=choke_points_count,
            generated_at=datetime.now(timezone.utc).isoformat()
        )

        return DigitalTwinGraphResponse(nodes=nodes, edges=edges, summary=summary)

    def calculate_attack_paths(self, req: AttackPathRequest) -> AttackPathResponse:
        """Discovers all traversable attack paths between source and target, ranked by exploitability."""
        source = req.source_node_id
        target = req.target_node_id

        if source not in self.graph:
            raise ValueError(f"Source node '{source}' not found in Digital Twin graph.")
        if target not in self.graph:
            raise ValueError(f"Target node '{target}' not found in Digital Twin graph.")

        # Find paths using NetworkX all_simple_paths
        raw_paths = []
        try:
            raw_paths = list(nx.all_simple_paths(self.graph, source, target, cutoff=req.max_hops))
        except Exception:
            pass

        # If no direct directed path exists, try shortest path or reverse traversal for resilient analysis
        if not raw_paths:
            try:
                shortest = nx.shortest_path(self.graph, source, target, weight="weight")
                raw_paths = [shortest]
            except Exception:
                raw_paths = []

        attack_paths: List[AttackPathItem] = []
        centrality = nx.betweenness_centrality(self.graph)

        for idx, path_nodes in enumerate(raw_paths[:5]):  # Top 5 most prominent paths
            steps: List[AttackPathStep] = []
            cumulative_risk = 0.0

            for hop_idx in range(len(path_nodes) - 1):
                u = path_nodes[hop_idx]
                v = path_nodes[hop_idx + 1]
                u_node = self.nodes_dict.get(u)
                v_node = self.nodes_dict.get(v)
                edge_data = self.graph.get_edge_data(u, v) or {}

                u_label = u_node.label if u_node else u
                v_label = v_node.label if v_node else v

                # Map realistic MITRE ATT&CK techniques based on source/dest zones
                if hop_idx == 0:
                    tech_id, tech_name, tactic = "T1190", "Exploit Public-Facing Application", "Initial Access"
                    desc = f"Attacker leverages exposed edge ports to gain initial footprint on {v_label}."
                elif v_node and v_node.zone == "SECURE_VAULT":
                    tech_id, tech_name, tactic = "T1003.008", "/etc/shadow & Credential Vault Access", "Credential Access / Exfiltration"
                    desc = f"Adversary targets crown jewel {v_label} to dump credentials and sensitive databases."
                elif v_node and "firewall" in (v_node.device_type or "").lower():
                    tech_id, tech_name, tactic = "T1562.001", "Disable or Evade Security Tools", "Defense Evasion"
                    desc = f"Attacker bypasses filtering on {v_label} using tunneled protocols."
                elif v_node and "VULNERABLE_TARGET" in (v_node.security_tags or []):
                    tech_id, tech_name, tactic = "T1068", "Exploitation for Privilege Escalation", "Privilege Escalation"
                    desc = f"Attacker executes unpatched RCE vulnerability on {v_label}."
                else:
                    tech_id, tech_name, tactic = "T1021.004", "SSH & Lateral Movement Protocol", "Lateral Movement"
                    desc = f"Attacker pivots through internal network from {u_label} to {v_label}."

                step_risk = (v_node.risk_score if v_node else 50) * 0.4 + (edge_data.get("weight", 1.0) * 10)
                cumulative_risk += step_risk

                steps.append(AttackPathStep(
                    hop_number=hop_idx + 1,
                    source_node_id=u,
                    source_label=u_label,
                    target_node_id=v,
                    target_label=v_label,
                    technique_id=tech_id,
                    technique_name=tech_name,
                    tactic=tactic,
                    protocol=edge_data.get("protocol", "TCP"),
                    port=edge_data.get("ports", [None])[0] if edge_data.get("ports") else None,
                    risk_weight=round(step_risk, 1),
                    description=desc
                ))

            normalized_risk = min(100, int(cumulative_risk / max(1, len(steps)) + 20))
            viability = "HIGH" if normalized_risk > 65 else "MEDIUM" if normalized_risk > 40 else "LOW"

            # Identify choke points in this path: intermediate nodes with high centrality
            path_choke_points = [
                nid for nid in path_nodes[1:-1]
                if centrality.get(nid, 0) > 0.15
            ]

            mitigation = f"Deploy restrictive nftables rule at {path_choke_points[0]} to sever this vector" if path_choke_points else "Quarantine intermediary nodes via SOAR playbook."

            attack_paths.append(AttackPathItem(
                path_id=f"path-{str(uuid.uuid4())[:8]}",
                node_sequence=path_nodes,
                node_labels=[self.nodes_dict[n].label if n in self.nodes_dict else n for n in path_nodes],
                hops=len(path_nodes) - 1,
                cumulative_risk=normalized_risk,
                viability=viability,
                steps=steps,
                choke_point_node_ids=path_choke_points,
                mitigation_summary=mitigation
            ))

        # Overall recommended choke point is the one appearing most across all paths
        choke_counter: Dict[str, int] = {}
        for p in attack_paths:
            for cp in p.choke_point_node_ids:
                choke_counter[cp] = choke_counter.get(cp, 0) + 1
        top_cp = max(choke_counter, key=choke_counter.get) if choke_counter else None

        shortest_hops = min([p.hops for p in attack_paths]) if attack_paths else 0

        return AttackPathResponse(
            source_node_id=source,
            target_node_id=target,
            total_paths_found=len(attack_paths),
            shortest_path_hops=shortest_hops,
            recommended_choke_point=self.nodes_dict[top_cp].label if top_cp and top_cp in self.nodes_dict else top_cp,
            paths=attack_paths
        )

    def calculate_blast_radius(self, asset_id: str) -> BlastRadiusResponse:
        """Calculates downstream reachability and blast score if asset_id is compromised."""
        if asset_id not in self.graph:
            raise ValueError(f"Asset '{asset_id}' not found in Digital Twin graph.")

        origin_node = self.nodes_dict.get(asset_id)
        origin_label = origin_node.label if origin_node else asset_id

        # Downstream reachable nodes via BFS / shortest path lengths
        lengths = nx.single_source_shortest_path_length(self.graph, asset_id)
        # Remove self from reachable downstream
        reachable_ids = [nid for nid in lengths if nid != asset_id]

        reachable_assets: List[ReachableAssetDetail] = []
        by_criticality: Dict[str, int] = {
            AssetCriticality.CRITICAL: 0,
            AssetCriticality.HIGH: 0,
            AssetCriticality.MEDIUM: 0,
            AssetCriticality.LOW: 0,
        }
        by_zone: Dict[str, int] = {}

        weighted_threat = 0.0

        for nid in reachable_ids:
            node = self.nodes_dict.get(nid)
            if not node:
                continue

            crit = node.criticality or AssetCriticality.LOW
            by_criticality[crit] = by_criticality.get(crit, 0) + 1
            by_zone[node.zone] = by_zone.get(node.zone, 0) + 1

            hops = lengths.get(nid, 1)

            # Weighting factors: proximity and criticality
            crit_weight = 40.0 if crit == AssetCriticality.CRITICAL else 25.0 if crit == AssetCriticality.HIGH else 10.0
            distance_discount = 1.0 / max(1, hops)
            weighted_threat += crit_weight * distance_discount

            impact = f"{crit} impact: Direct network reachability at {hops} hop(s)."
            if node.zone == "SECURE_VAULT":
                impact = "CRITICAL: Direct attack avenue into high-security crown jewel vault!"

            reachable_assets.append(ReachableAssetDetail(
                node_id=nid,
                label=node.label,
                node_type=node.node_type,
                zone=node.zone,
                criticality=crit,
                risk_score=node.risk_score,
                hops_away=hops,
                impact_summary=impact
            ))

        # Sort reachable assets by criticality then proximity
        crit_rank = {AssetCriticality.CRITICAL: 4, AssetCriticality.HIGH: 3, AssetCriticality.MEDIUM: 2, AssetCriticality.LOW: 1}
        reachable_assets.sort(key=lambda a: (-crit_rank.get(a.criticality, 0), a.hops_away))

        # Calculate final blast score (0 - 100)
        blast_score = min(100, int(weighted_threat * 1.5 + (len(reachable_assets) * 5)))

        # Recommended containment playbook
        recommendation = "Host containment recommended immediately."
        playbook = "playbook-host-quarantine"
        if origin_node and origin_node.node_type == DigitalTwinNodeType.DEVICE:
            recommendation = "Enforce emergency firewall segmentation rule on transit interface."
            playbook = "playbook-block-attacker-ip"

        return BlastRadiusResponse(
            node_id=asset_id,
            node_label=origin_label,
            blast_score=blast_score,
            total_reachable_nodes=len(reachable_assets),
            reachable_by_criticality=by_criticality,
            reachable_by_zone=by_zone,
            reachable_assets=reachable_assets,
            containment_recommendation=recommendation,
            playbook_to_execute=playbook
        )

    def identify_choke_points(self) -> ChokePointResponse:
        """Identifies optimal defensive choke points using NetworkX betweenness centrality."""
        centrality = nx.betweenness_centrality(self.graph, weight="weight")
        choke_items: List[ChokePointItem] = []

        total_nodes = len(self.graph.nodes())
        critical_targets = [nid for nid, n in self.nodes_dict.items() if n.criticality == AssetCriticality.CRITICAL]

        # Filter out leaf endpoints and examine candidate transit nodes
        for nid, score in sorted(centrality.items(), key=lambda x: x[1], reverse=True):
            node = self.nodes_dict.get(nid)
            if not node:
                continue

            # Skip external adversary node or pure leaves
            if node.zone == "EXTERNAL" or self.graph.degree(nid) <= 1:
                continue

            # Calculate how many critical targets depend on this node for transit
            paths_shielded = 0
            for crit_id in critical_targets:
                if crit_id == nid:
                    continue
                # If removing nid disconnects external adversary from crit_id
                G_copy = self.graph.copy()
                G_copy.remove_node(nid)
                if not nx.has_path(G_copy, "node-adversary-ext-01", crit_id) and nx.has_path(self.graph, "node-adversary-ext-01", crit_id):
                    paths_shielded += 1

            intercepted_pct = round(score * 100.0, 1)
            risk_level = "CRITICAL" if score > 0.25 else "HIGH" if score > 0.12 else "MEDIUM"

            rec = f"Apply zero-trust inspection and block unauthorized transit on {node.label}."
            action = "ENFORCE_FIREWALL_FILTER" if "firewall" in (node.device_type or "").lower() or "router" in (node.device_type or "").lower() else "DEPLOY_AGENT_EDR"

            choke_items.append(ChokePointItem(
                node_id=nid,
                label=node.label,
                node_type=node.node_type,
                zone=node.zone,
                betweenness_centrality=round(score, 4),
                paths_intercepted_pct=intercepted_pct,
                critical_assets_shielded=paths_shielded,
                risk_level=risk_level,
                recommendation=rec,
                suggested_action=action
            ))

        top_id = choke_items[0].node_id if choke_items else None
        summary_msg = f"Identified {len(choke_items)} defensive transit choke points. Top priority: {choke_items[0].label if choke_items else 'None'}."

        return ChokePointResponse(
            choke_points=choke_items[:8],
            top_recommended_node_id=top_id,
            summary=summary_msg
        )
