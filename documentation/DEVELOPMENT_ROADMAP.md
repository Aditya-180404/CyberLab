# CyberLab Development Roadmap

This roadmap documents the 12-phase incremental delivery plan for Project CyberLab.

---

## Roadmap Overview

```
[Phase 1: Core Foundation] (Current)
           │
[Phase 2: Network Simulation Engine]
           │
[Phase 3: Real VM Integration]
           │
[Phase 4: Distributed Linux Agent]
           │
[Phase 5: Asset Inventory & Monitoring]
           │
[Phase 6: SIEM & Detection Engine]
           │
[Phase 7: Incident Response (SOAR)]
           │
[Phase 8: Digital Twin & Attack Paths]
           │
[Phase 9: Attack Simulation Studio]
           │
[Phase 10: Purple-Team Validation]
           │
[Phase 11: Vulnerability Management & SOAR]
           │
[Phase 12: Multi-Site & Enterprise Readiness]
```

---

## Phase Details

### Phase 1: Core Foundation (Current Target)
- Modular project structure (`backend/`, `frontend/`, `agent/`, `documentation/`).
- FastAPI backend with Pydantic settings, structured logging, global exception handling, and security middleware.
- Database layer with SQLAlchemy 2.0 and SQLite (with PostgreSQL migration path).
- Core security: Password hashing, JWT token authentication, and RBAC roles (`SuperAdmin`, `OrgAdmin`, `SOCManager`, `SOCAnalyst`, `NetworkEngineer`, `Auditor`).
- Health and system diagnostic API (`/api/v1/health`).
- Audit logging pipeline.
- Next.js TypeScript frontend with Tailwind CSS, Lucide icons, dark SOC styling, and live backend connection.
- Automated pytest suite and verification procedures.

### Phase 2: Linux Network Simulation Engine
- Linux network namespace (`netns`) lifecycle management.
- Virtual Ethernet (`veth`) pair creation and routing.
- Linux bridge and VLAN-aware filtering integration.
- `nftables` programmatic rule builder for simulated firewalls.
- Safety boundaries preventing mutation of physical and Wi-Fi host interfaces.
- Visual network topology builder with `@xyflow/react`.

### Phase 3: Real VM Integration
- VMware Workstation CLI (`vmrun`) adapter.
- VM inventory discovery, power control (`start`, `stop`, `reset`, `suspend`).
- Virtual network adapter inspection and bridging to CyberLab virtual switches.
- Error handling, connection status monitoring, and audit trails.

### Phase 4: Distributed Linux Agent Platform
- Standalone Python Linux agent with automated registration.
- Agent identity, secure token generation, and credential revocation.
- Outbound TLS/WebSocket heartbeat and health reporting.
- Command allowlisting and offline policy persistence.

### Phase 5: Asset Inventory & Monitoring
- Endpoint hardware, OS, kernel, and network inventory collection.
- Process tree monitoring and suspicious execution flags.
- Real-time network socket monitoring (listening ports, active connections).
- Authentication monitoring (`/var/log/auth.log`, sudo invocations).
- File Integrity Monitoring (FIM) for critical system paths.
- Central endpoint management dashboard.

### Phase 6: SIEM & Detection Engine
- High-throughput event ingestion and normalization schema.
- Detection rule engine (threshold, pattern matching, time-window analysis).
- MITRE ATT&CK taxonomy tagging (Tactics and Techniques).
- Multi-host correlation engine and incident generation.
- Evidence-based root-cause analysis (RCA) pipeline.

### Phase 7: Incident Response (SOAR)
- Incident lifecycle management (`New`, `Open`, `Investigating`, `Contained`, `Resolved`, `Closed`).
- Evidence graph and analyst investigation workspace.
- Response workflows: Host isolation, IP blocking, firewall rule deployment, service restart.
- Human-in-the-loop approval gates, verification probes, and rollback state machine.

### Phase 8: Digital Twin & Attack Paths
- In-memory NetworkX topological graph built from live asset data.
- Layer 2/3 connectivity analysis and reachability matrix.
- Attack-path discovery based on open ports, services, and firewall barriers.
- Blast-radius impact traversal and what-if simulation scenarios.

### Phase 9: Attack Simulation Studio
- Safe, bounded offensive simulation engine.
- Scenarios: Port scanning, SSH brute-force generation, suspicious process execution, lateral movement probes.
- Target authorization check: strictly restricted to managed CyberLab nodes.
- Automated validation of detection alert generation.

### Phase 10: Purple-Team Security Validation
- Continuous security control validation framework.
- Automated execution of adversary tactics paired with control effectiveness scoring.
- Pass/Fail scoring matrix for firewall, EDR, FIM, and SIEM rules.
- Historical trend reports and remediation recommendations.

### Phase 11: Vulnerability Management & SOAR
- Vulnerability scan ingestion (NVD, OpenVAS, Trivy adapters).
- CVE mapping, CVSS scoring, and contextual asset risk weighting.
- Automated patch/remediation workflow with approval checkpoints.

### Phase 12: Multi-Site & Enterprise Readiness
- Multi-tenant Organization and Site isolation.
- Distributed agent fleet management across remote branch offices.
- Production PostgreSQL migration and database replication.
- Hardened deployment (systemd services, containerization, TLS certificate automation).
