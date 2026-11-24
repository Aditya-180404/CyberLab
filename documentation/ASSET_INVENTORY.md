# CyberLab Unified Asset Inventory & Risk Posture Engine (Phase 5)

## 1. Architectural Overview

In a hybrid cybersecurity research lab and SOC operations environment, assets originate from disparate infrastructure layers:
1. **Real Virtual Machines**: VMware Workstation (and future QEMU/KVM) hypervisor guests, including vulnerable attack targets (Metasploitable 2, Stapler, Kioptrix, VulnHub) and analysis workstations (Parrot OS, Windows Server).
2. **Distributed Linux Endpoints**: Physical workstations and target virtual machines running the autonomous `cyberlab_agent.py` EDR agent streaming live socket, process, and file integrity telemetry.
3. **Simulated Network Infrastructure**: Network namespaces, Linux bridges, routers, firewalls, and switches orchestrated inside the CyberLab Network Studio.

Prior to Phase 5, these assets existed as siloed entities. The **Unified Asset Inventory Engine** harmonizes, deduplicates, and continuously scores the security posture of every asset across the entire enterprise estate.

```
+-----------------------------------------------------------------------------------+
|                        CYBERLAB UNIFIED ASSET INVENTORY                           |
+-----------------------------------------------------------------------------------+
             ^                                  ^                             ^
             |                                  |                             |
+--------------------------+       +--------------------------+       +------------------------+
|  VMware Virtual Machines |       |  Distributed EDR Agents  |       |  Simulated Topologies  |
|  - .vmx Configuration    |       |  - Outbound TLS Tokens   |       |  - Linux Namespaces    |
|  - Power State           |       |  - Open Sockets/Ports    |       |  - Virtual Bridges     |
|  - Virtual Adapters      |       |  - Process Snapshots     |       |  - nftables Firewalls  |
|  - Vulnerable Target Tag |       |  - FIM Hash Deltas       |       |  - IP/MAC Routing      |
+--------------------------+       +--------------------------+       +------------------------+
```

---

## 2. Normalized Data Model

The `Asset` relational entity (`assets` table) stores the aggregated profile:

| Field | Type | Description |
|---|---|---|
| `id` | `String(36)` | Unique asset identifier (e.g. `asset-a8f3b190`). |
| `name` | `String(100)` | Canonical display name / hostname. |
| `asset_type` | `String(30)` | `VIRTUAL_MACHINE`, `AGENT_HOST`, `SIMULATED_DEVICE`, `PHYSICAL_HOST`. |
| `ip_addresses_json` | `Text (JSON)` | List of discovered IPv4 / IPv6 addresses. |
| `mac_addresses_json` | `Text (JSON)` | List of physical/virtual MAC addresses. |
| `os_family` | `String(50)` | `Linux`, `Windows`, `BSD`, `NetworkOS`. |
| `os_version` | `String(100)` | OS release / distribution details. |
| `kernel_version` | `String(100)` | Running Linux kernel version. |
| `criticality` | `String(20)` | Business impact tier (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`). |
| `risk_score` | `Integer` | Continuous security posture score (`0` to `100`). |
| `exposure` | `String(20)` | Network placement (`INTERNAL`, `ISOLATED`, `DMZ`, `PUBLIC`). |
| `status` | `String(20)` | `ACTIVE`, `INACTIVE`, `QUARANTINED`, `DECOMMISSIONED`. |
| `services_json` | `Text (JSON)` | Open listening ports, protocols, and daemon states. |
| `security_tags_json` | `Text (JSON)` | Real-time threat & architecture tags (`VULNERABLE_TARGET`, `BRIDGED_ADAPTER`, `EDR_MONITORED`, `FIM_ALERT_ACTIVE`, `SECURITY_GATEWAY`). |

---

## 3. Dynamic Security Risk Scoring Algorithm

Asset risk is dynamically computed on a normalized scale from **0 to 100**:

$$\text{Risk Score} = \min\left(100, \text{Base} + W_{\text{vuln}} + W_{\text{bridge}} + W_{\text{state}} + W_{\text{fim}} + \sum W_{\text{ports}} + W_{\text{quarantine}}\right)$$

### Scoring Factors:
1. **Baseline Exposure**: $+10$ points for all active network nodes.
2. **Known Vulnerable Asset**: $+55$ points if flagged as an intentionally vulnerable testing machine (Metasploitable, Stapler, Kioptrix).
3. **Dangerous Network Exposure**: $+25$ points if a vulnerable asset has a bridged network adapter connected directly to the user's physical LAN.
4. **Active Execution Exposure**: $+5$ points if the virtual machine is actively powered on.
5. **File Integrity Violations**: $+15$ points per active FIM alert (capped at $+30$) when `/etc/passwd`, `/etc/shadow`, or `/etc/sudoers` hashes change unexpectedly.
6. **Unencrypted / Legacy Listening Services**:
   - $+10$ points for legacy unencrypted protocols: FTP (Port 21), Telnet (Port 23), HTTP (Port 80), POP3 (Port 110), IMAP (Port 143).
   - $+3$ points for privileged root listening ports ($< 1024$).
7. **Quarantine / Compromise State**: $+15$ points if under active SOAR network quarantine; $+25$ points if credentials have been revoked due to administrative killswitch.

---

## 4. REST API Endpoints

All endpoints require JWT Bearer authentication:

| Method | Endpoint | Description | Required RBAC Role |
|---|---|---|---|
| `GET` | `/api/v1/assets` | Filterable asset list (`asset_type`, `criticality`, `min_risk`, `search`). | All Authenticated Users |
| `GET` | `/api/v1/assets/kpis` | Fleet-wide KPI metrics (averages, counts by tier). | All Authenticated Users |
| `POST` | `/api/v1/assets/sync` | Re-scans VMs, Agents, and Topologies into unified Asset records. | Super Admin, SOC Manager, Analyst, Engineer |
| `GET` | `/api/v1/assets/{id}` | Deep posture inspection including underlying source details. | All Authenticated Users |
| `PUT` | `/api/v1/assets/{id}/criticality` | Reclassifies business criticality (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`). | Super Admin, SOC Manager, Analyst |

---

## 5. Security & Isolation Controls

1. **Non-Destructive Synchronization**: Synchronizing assets never halts virtual machines or disrupts agent communication.
2. **Permanent Host Protection**: Assets never alter or bind to the physical host's primary interfaces (`wlan0`, `eth0`, `lo`, default route).
3. **Immutable Audit Logging**: Every manual asset reclassification or synchronization trigger is written to the append-only `audit_logs` table.
