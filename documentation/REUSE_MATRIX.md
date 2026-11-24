# CyberLab Component Reuse & Adaptation Matrix

**Reference Analysis Target**: `https://github.com/Samar2442/NETGUARDIAN`  
**Standard**: ISO/IEC clean-room software engineering & legal compliance.

---

## 1. Classification Definitions

- **REUSE**: Direct code adoption permitted by license and technically suitable (0% applicable due to missing repository license).
- **ADAPT**: Architectural design pattern, state machine, or workflow model adapted and re-engineered for CyberLab.
- **REIMPLEMENT**: Independent, clean-room implementation of a capability from first principles with CyberLab's enterprise specifications.
- **REJECT**: Component, pattern, or implementation rejected due to insecurity, lack of license, or incompatibility.

---

## 2. Detailed Component Matrix

| Subsystem / Capability | NETGUARDIAN Status | Classification | Technical Rationale & CyberLab Strategy |
|---|---|---|---|
| **Frontend UI (Vite / React SPA)** | Vite + React 18 SPA | **REJECT** | CyberLab uses **Next.js with TypeScript and Tailwind CSS**. Next.js provides App Router architecture, API route proxying, and strict enterprise code splitting. Source code cannot be copied due to licensing. |
| **Topology Rendering Engine** | React Flow (@xyflow/react) | **ADAPT** | Concept of using `@xyflow/react` for interactive topology nodes is validated. CyberLab will write custom nodes for Linux bridges, namespaces, firewalls, and VMs with real-time WebSocket state badges. |
| **Backend REST Core** | FastAPI + Pydantic v2 | **REIMPLEMENT** | FastAPI + Pydantic is already the chosen technology for CyberLab. Built from scratch with modular sub-routers, strict dependency injection, and fine-grained exception handling. |
| **Database Schema & ORM** | SQLAlchemy 2.0 + SQLite | **REIMPLEMENT** | Clean-room implementation of SQLAlchemy models. CyberLab models will support multi-site, distributed agents, MITRE ATT&CK mappings, and Linux network resources. |
| **Network Graph & Blast Radius** | NetworkX Graph algorithms | **ADAPT** | In-memory graph modeling via NetworkX is mathematically sound. CyberLab will adapt the algorithm to model Linux network namespaces, routing tables, and firewall filter barriers rather than Cisco trunks. |
| **RCA / Diagnostic Rules** | Hardcoded Cisco CCNA Rules | **REJECT** | Cisco CLI syntax checks (e.g. `switchport trunk allowed vlan`) are irrelevant to Linux kernel namespaces, nftables, and distributed Linux agents. |
| **Security Event Normalization** | Simple event dict | **REIMPLEMENT** | CyberLab implements a formal ECS/SIEM-aligned schema (`EventID`, `AgentID`, `Host`, `Source/Dest IP`, `Category`, `MITRE Tactic/Technique`, `RawPayload`). |
| **Remediation State Machine** | Multi-step approval & rollback | **ADAPT** | The approval lifecycle (`PROPOSED` -> `PENDING_APPROVAL` -> `EXECUTED` -> `VERIFIED` / `ROLLED_BACK`) is sound. CyberLab will adapt this pattern for host isolation, nftables rule manipulation, and service remediation. |
| **Live Telemetry Engine** | FastAPI WebSockets | **REIMPLEMENT** | Built cleanly with WebSocket connection manager supporting channel-based subscriptions (e.g. topology updates, agent telemetry streams, incident alerts). |
| **Cisco CLI Execution (Netmiko/SSH)**| Unrestricted SSH commands | **REJECT** | Fundamentally unsafe for automated response. CyberLab requires strict command allowlisting, non-root execution wrappers, and auditable parameter validation. |
| **Endpoint Security & Agent** | Absent in NETGUARDIAN | **REIMPLEMENT** | Entirely new subsystem for CyberLab: Python-based Linux agent with heartbeat, system inventory, process monitoring, authentication logs, and FIM. |
| **Attack Simulation & Purple Team** | Absent in NETGUARDIAN | **REIMPLEMENT** | Entirely new subsystem for CyberLab: controlled, bounded test scenarios with automated control validation and pass/fail scoring. |
| **VMware / QEMU Virtualization** | Absent in NETGUARDIAN | **REIMPLEMENT** | Entirely new subsystem for CyberLab: hypervisor adapter layer for real VM power state management and network interface association. |
