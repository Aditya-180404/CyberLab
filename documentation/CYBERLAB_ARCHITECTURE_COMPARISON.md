# CyberLab Architecture Comparison: CyberLab vs. NetGuardian

This document establishes the architectural distinction between **CyberLab** and the reference project **NetGuardian**.

---

## 1. High-Level Comparison Matrix

| Architectural Dimension | NetGuardian Reference | CyberLab Platform |
|---|---|---|
| **Primary Domain** | Network management & CCNA training | Hybrid Cybersecurity Infrastructure, SOC, SIEM & Purple-Team Platform |
| **Target Infrastructure** | Simulated Cisco IOS devices (switches, routers) | Real Linux network namespaces, veth pairs, Linux bridges, nftables, VMware Workstation VMs |
| **Frontend Architecture** | React 18 + Vite SPA | Next.js (App Router) + TypeScript + Tailwind CSS |
| **Backend Architecture** | FastAPI monolith with utility engines | Modular FastAPI with domain-driven design, isolated services, and strict privilege barriers |
| **Endpoint Security / EDR** | None | Distributed Linux Agent (Inventory, Process, Auth, FIM, Network, Isolation) |
| **Threat Detection / SIEM** | Rule-based network fault checks | Multi-source SIEM ingestion, MITRE ATT&CK mapping, correlation engine, and RCA |
| **Offensive / Validation** | None | Attack Simulation Studio & Purple-Team Control Validation Engine |
| **Automated Response (SOAR)**| Cisco CLI reconfiguration | Policy-controlled SOAR (IP blocking, nftables enforcement, endpoint isolation, service control) |
| **Execution Security Model**| Unrestricted SSH / mock CLI strings | Principle of Least Privilege, scoped helper services, command allowlisting, strict RBAC |
| **Multi-Site Readiness** | Single environment focus | Hierarchical Site & Organization architecture |

---

## 2. Deep-Dive Architectural Differences

### 2.1 Infrastructure & Simulation Engine
- **NetGuardian**: Relies on mock objects or remote Cisco devices polled via Netmiko and SNMP. It does not create or manage virtualization or host networking natively.
- **CyberLab**: Directly orchestrates Linux kernel networking features:
  - `ip netns` creates real network isolation domains.
  - `veth` pairs provide high-throughput interconnects between namespaces and bridges.
  - `nftables` enforces real packet filtering and NAT.
  - Hypervisor adapters (VMware Workstation CLI `vmrun` / QEMU `virsh`) manage real virtual machines connected to lab bridges.

### 2.2 Security Operations (SOC) & SIEM
- **NetGuardian**: Captures basic network interface flapping and reachability loss.
- **CyberLab**: Ingests comprehensive security telemetry:
  - Auditd / SSH authentication logs (`/var/log/auth.log` or systemd journal).
  - Process creation events and parent-child execution trees.
  - File Integrity Monitoring (FIM) SHA-256 baseline deltas for `/etc`, `/bin`, `/usr/bin`.
  - Network connection sockets (listening ports, remote connections).
  - Normalization to a unified schema cross-referenced with MITRE ATT&CK tactics (Reconnaissance, Execution, Persistence, Lateral Movement, Exfiltration).

### 2.3 Offensive Simulation & Purple-Team Validation
- **NetGuardian**: Has no offensive simulation or control validation capabilities.
- **CyberLab**: Houses an integrated Attack Simulation Studio that can safely trigger bounded tests (e.g., failed SSH logins, port scans, benign test process execution) against designated lab nodes, verifying that:
  1. The agent captures the telemetry.
  2. The detection engine triggers the expected rule.
  3. The SOC creates the incident.
  4. The SOAR response executes verified containment.

### 2.4 Governance & Safety Boundaries
- **NetGuardian**: Allows arbitrary script proposal without host sandboxing.
- **CyberLab**: Strictly separates web application privileges from system networking:
  - The FastAPI backend runs as an unprivileged user (`ghost`).
  - Network-layer and firewall alterations require authenticated, rate-limited, and audited execution through tightly scoped helper scripts with strict parameter validation.
  - Critical host interfaces (e.g. primary WAN, Wi-Fi `wlan0`, host default gateway) are hardcoded into an immutable protection exclusion list.
