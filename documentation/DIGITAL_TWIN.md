# CyberLab Digital Twin & Attack-Path Analysis Engine (Phase 8)

## 1. Overview & Purpose

The **CyberLab Digital Twin Engine** provides real-time topological graph modeling, attack path discovery, blast-radius quantification, and defensive choke-point identification.

Unlike decorative network diagrams, CyberLab's Digital Twin is built on **NetworkX** directed multigraph algorithms (`DiGraph`), continuously synchronizing live state from:
1. **Asset Inventory**: Real discovered hosts, operating systems, criticality, open listening ports, and risk scores.
2. **Virtual Machine Hypervisor Adapter**: Local VMware Workstation VMs (e.g., `Metasploitable2-Linux`, `Parrot`, `Opensence`).
3. **Simulated Linux Topologies**: Network namespaces, bridges, veth connections, and nftables firewall state.
4. **SIEM & Security Telemetry**: Active security incidents and critical detections flagging compromised nodes in real time.

---

## 2. Topological Architecture & Security Zones

The Digital Twin organizes infrastructure into canonical defense-in-depth zones:

```
[Zone: EXTERNAL / WAN]
       │
       ▼ (Probing / Port Scans)
[Zone: PERIMETER / FIREWALL]  ─── (nftables State Inspection)
       │
       ▼ (Ingress Forwarding: 80, 443)
[Zone: DMZ REVERSE PROXY]
       │
       ▼ (DMZ to Internal Transit: 8080, 8443, 22)
[Zone: CORE TRANSIT ROUTER]   ◄─── (Central Choke Point)
    ▲             ▲
    │             │ (Internal LAN: SSH, SMB, RPC)
    │             ▼
    │      [Zone: INTERNAL LAN] (Discovered VMs & Linux Agents)
    │             │
    ▼             ▼ (Restricted Database Transit: 5432, 3306)
[Zone: SECURE DATABASE VAULT] (Crown Jewel: PII, Credentials, Secrets)
```

Each node possesses:
- `node_type`: `ASSET`, `DEVICE`, `SEGMENT`, or `ADVERSARY`
- `zone`: `EXTERNAL`, `DMZ`, `INTERNAL`, `SECURE_VAULT`, or `TRANSIT_ROUTER`
- `criticality`: `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL`
- `risk_score`: 0–100 calculated from asset vulnerabilities, exposures, and active incidents
- `is_compromised`: Boolean indicator dynamically set when active incidents or simulations occur

---

## 3. Attack-Path Discovery & MITRE ATT&CK Mapping

Adversaries traverse networks along paths of least resistance. The Digital Twin calculates all viable simple paths from an entrypoint to a target crown jewel:

$$\text{Path Risk} = \min\left(100, \frac{\sum \text{Step Risk}}{\text{Hops}} + 20\right)$$

Each hop is mapped to concrete MITRE ATT&CK tactics and techniques:
- **Hop 1: Initial Ingress**: `T1190` (*Exploit Public-Facing Application*) on DMZ reverse proxy / web gateway.
- **Hop 2: Defense Evasion**: `T1562.001` (*Disable or Evade Security Tools*) on transit filters.
- **Hop 3: Lateral Movement**: `T1021.004` (*SSH Remote Services*) / `T1046` (*Network Service Discovery*).
- **Hop 4: Privilege Escalation**: `T1068` (*Exploitation for Privilege Escalation*) / `T1548.003` (*Sudo and Sudo Caching*).
- **Hop 5: Target Impact**: `T1003.008` (*/etc/shadow & Credential Vault Access*).

---

## 4. Blast-Radius Quantification

When any host or device is compromised, the engine computes downstream reachability via directed breadth-first traversal (`nx.single_source_shortest_path_length`):

$$\text{Blast Score} = \min\left(100, \sum_{h \in \text{Reachable}} \frac{\text{Weight}(h)}{\text{Hop Distance}(h)} + (\text{Count} \times 5)\right)$$

Where weights reflect asset criticality:
- **CRITICAL**: 40.0 points
- **HIGH**: 25.0 points
- **MEDIUM / LOW**: 10.0 points

The blast radius analysis automatically outputs immediate SOAR containment recommendations (e.g., executing `playbook-host-quarantine` on the compromised host to sever lateral edges).

---

## 5. Defensive Choke-Point Optimization

Defenders cannot patch every vulnerability simultaneously. The Digital Twin applies **Betweenness Centrality** to identify structural bottlenecks:

$$C_B(v) = \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}$$

Nodes with high betweenness centrality (routers, core firewalls, transit jumpboxes) intercept the highest percentage of attack paths.
- **Top Priority**: Enforcing zero-trust ACLs or deep packet inspection at `node-core-router-01` intercepts over 80% of cross-zone lateral paths to the database vault.

---

## 6. Dynamic What-If Simulation

Security operators can simulate hypothetical compromise events without polluting historical telemetry logs:
- `POST /api/v1/digital-twin/simulate-compromise`: Flags any node as compromised and recalculates the digital twin posture in real time.
- `POST /api/v1/digital-twin/reset-simulation`: Clears transient what-if states back to the live baseline.

---

## 7. REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/digital-twin/graph` | Returns all nodes, directed edges, and summary metrics |
| `POST` | `/api/v1/digital-twin/attack-paths` | Discovers ranked attack paths with MITRE techniques |
| `GET` | `/api/v1/digital-twin/blast-radius/{asset_id}` | Calculates downstream reachability & blast score |
| `GET` | `/api/v1/digital-twin/choke-points` | Ranks transit nodes by NetworkX centrality |
| `POST` | `/api/v1/digital-twin/simulate-compromise` | Toggles transient compromise for what-if modeling |
| `POST` | `/api/v1/digital-twin/reset-simulation` | Resets transient simulation state |

---

## 8. Verification & Test Suite

The engine is validated with 7 automated pytest tests in `backend/tests/test_digital_twin.py`:
- `test_digital_twin_graph_construction`: Validates multi-zone node generation and edge weights.
- `test_attack_path_discovery`: Validates end-to-end path finding and MITRE ATT&CK technique mapping.
- `test_attack_path_invalid_node`: Validates 404/ValueError handling on non-existent targets.
- `test_blast_radius_calculation`: Validates downstream reachability and SOAR containment recommendations.
- `test_choke_point_identification`: Validates betweenness centrality calculations.
- `test_simulate_compromise_and_reset`: Validates what-if simulation toggling.
- `test_digital_twin_api_endpoints`: Validates authenticated REST API calls.

Total backend test suite: **52 passing tests**.
Frontend production build: **Compiled successfully with zero TypeScript errors**.
