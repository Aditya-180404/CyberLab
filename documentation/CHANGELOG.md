# CyberLab Changelog

All notable changes to the CyberLab platform are documented in this file.

---

## [Phase 5: Asset Inventory & Deep Monitoring Engine] - 2026-11-24

### Added
- **Unified Asset Inventory Engine (`backend/app/inventory/asset_manager.py`)**:
  - `AssetManager`: Harmonizes and deduplicates entities across VMware virtual machines, distributed Linux agents, and simulated network topology nodes.
  - Dynamic Security Risk Scoring (0 to 100): Weighted formula accounting for known vulnerable assets (Metasploitable +55), bridged exposure (+25), active runtime state (+5), FIM integrity violations (+15 to +30), unencrypted legacy services (FTP, Telnet, HTTP +10 each), and quarantine states.
  - Multi-source entity reconciliation: Automatically extracts virtual network adapters, MAC addresses, IP addresses, listening network daemons, and hardware specs.
- **Relational Models & Schemas (`backend/app/models/asset.py`, `backend/app/schemas/asset.py`)**:
  - `Asset`: Canonical entity storing system fingerprints, business criticality (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), risk score, exposure, services JSON, security tags, and foreign key linkages to VMs, Agents, and Network Devices.
  - Pydantic v2 schemas: `AssetResponse`, `AssetDetailResponse`, `AssetCriticalityUpdateRequest`, `AssetSyncResult`, `AssetInventoryKPIs`.
- **REST API Endpoints (`backend/app/api/v1/assets.py`)**:
  - `GET /api/v1/assets`: Searchable and filterable asset catalog (filter by `asset_type`, `criticality`, `min_risk`, or hostname/IP query).
  - `GET /api/v1/assets/kpis`: Aggregated fleet metrics, average risk score, high-risk asset count, and breakdown by category.
  - `POST /api/v1/assets/sync`: Multi-source synchronization orchestrator importing and updating all platform entities with audit logging.
  - `GET /api/v1/assets/{id}`: Deep posture inspection returning underlying VM configurations, agent telemetry, and listening services.
  - `PUT /api/v1/assets/{id}/criticality`: Analyst reclassification of business criticality tier and network exposure.
- **SOC Asset Inventory Dashboard (`frontend/src/components/inventory/AssetInventory.tsx`)**:
  - Fleet KPI cards: Total assets, average risk score with color-coded gauge, high-risk asset counter, and critical asset counter.
  - Real-time search by hostname, IP address, or OS distribution.
  - Multi-dimensional filter pills: Asset class (`All`, `VMs`, `Agents`, `Simulated`) and Criticality tier (`All`, `Critical`, `High`, `Medium`, `Low`).
  - Interactive Asset Table: Shows OS details, IP addresses, visual risk meter, dynamic threat tags (`VULNERABLE_TARGET`, `BRIDGED_ADAPTER`, `EDR_MONITORED`, `FIM_ALERT_ACTIVE`), and inline criticality selector.
  - Deep Posture Details Modal: Hardware profile, open listening sockets table, underlying hypervisor or agent details, and risk factors summary.
  - One-click "Sync Multi-Source Assets" button.
- **Automated Tests (`backend/tests/test_asset_inventory.py`)**:
  - 4 comprehensive tests verifying multi-source entity synchronization, risk calculation for vulnerable targets, filtering, search, KPI aggregations, and RBAC criticality updates.
  - Full backend test suite expanded to 34 passing tests.
- **Documentation**:
  - `documentation/ASSET_INVENTORY.md`: Architecture guide, data model specification, scoring formula, and API reference.

---

## [Phase 4: Distributed Linux Agent Platform] - 2026-11-24

### Added
- **Distributed Linux Security Agent (`agent/cyberlab_agent.py`)**:
  - Autonomous lightweight Python agent installable on Kali host, Parrot OS VM, Metasploitable 2 VM, or remote Linux endpoints.
  - Automatic identity provisioning and outbound cryptographic credential exchange (`cla_` Bearer tokens).
  - Outbound TLS heartbeat reporting activity status and receiving SOAR control directives.
  - Host telemetry engine: CPU, memory, and disk utilization, listening network sockets mapping (`TCP`/`UDP` ports and connection states), and process snapshot collection.
  - File Integrity Monitoring (FIM): SHA-256 cryptographic baseline hashing and delta change detection on `/etc/passwd`, `/etc/shadow`, `/etc/sudoers`, `/etc/ssh/sshd_config`, and `/etc/hosts` with an alert buffer.
  - Local config persistence (`cyberlab_agent_config.json`) ensuring resilience across network drops and reboots.
- **Relational Models & Schemas (`backend/app/models/agent.py`, `backend/app/schemas/agent.py`)**:
  - `Agent`: Host entity tracking hardware specs, OS release, kernel version, status (`ONLINE`, `OFFLINE`, `ISOLATED`, `REVOKED`), policy JSON, and queued SOAR commands.
  - `AgentTelemetry`: Time-series table for host resource metrics, open sockets, processes, authentication events, and FIM alerts.
  - Pydantic v2 schemas: `AgentRegisterRequest`, `AgentHeartbeatRequest`, `AgentTelemetryBatch`, `AgentResponse`, `AgentDetailResponse`.
- **REST API Routes (`backend/app/api/v1/agents.py`)**:
  - `POST /api/v1/agents/register`: Self-registration endpoint issuing agent IDs and tokens.
  - `POST /api/v1/agents/heartbeat`: Authenticated periodic check-in returning queued SOAR commands.
  - `POST /api/v1/agents/telemetry`: Batch ingestion of host resource metrics, sockets, processes, and FIM alerts.
  - `GET /api/v1/agents`: SOC fleet overview with automatic offline detection (>35s heartbeat timeout).
  - `GET /api/v1/agents/{id}`: Detailed host telemetry snapshot and system specs.
  - `POST /api/v1/agents/{id}/isolate`: SOAR endpoint quarantine directive.
  - `POST /api/v1/agents/{id}/restore`: SOAR network restore directive.
  - `POST /api/v1/agents/{id}/revoke`: Immediate credential invalidation killswitch.
- **Frontend Endpoint Fleet Dashboard (`frontend/src/components/agent/EndpointFleet.tsx`)**:
  - Fleet KPI cards: Total endpoints, online nodes (live pulse), quarantined/isolated count, offline count.
  - Interactive agent list with hardware specs, IP addresses, OS/kernel details, and status badges.
  - Telemetry Inspection Modal displaying CPU/RAM/Disk gauges, active listening ports table, and FIM integrity alert logs.
  - Interactive SOAR controls: One-click "Quarantine / Isolate", "Restore Network", and "Revoke Credentials".
  - One-click copyable deploy command helper banner for easy onboarding of VMs.
- **Automated Tests (`backend/tests/test_agent.py`, `backend/tests/test_agent_e2e.py`)**:
  - 7 comprehensive tests covering registration, heartbeat authentication, telemetry ingestion, listing/details, SOAR isolation/restore lifecycle, credential revocation RBAC, and full end-to-end agent simulation.
  - Total test suite expanded to 30 passing tests.
- **Documentation**:
  - `documentation/AGENT_ARCHITECTURE.md`: Detailed specification of agent architecture, protocol lifecycle, FIM design, and SOAR response mechanics.

---

## [Phase 3: Real Virtual Machine Integration] - 2026-11-24

### Added
- **VMware Workstation Hypervisor Engine (`backend/app/vm/`)**:
  - `vmx_parser.py`: Safe `.vmx` configuration file parser extracting display names, vCPUs, memory, and virtual network adapters (`ethernet0` through `ethernet9`).
  - `vmware_adapter.py`: `VMwareWorkstationAdapter` using `/usr/bin/vmrun` CLI to query running VM instances and dispatch power operations (`start`, `stop`, `reset`, `suspend`).
  - `manager.py`: `VMManager` providing recursive filesystem discovery, safety validation, power state lifecycle management, and network segment association.
  - Automatic Vulnerable Asset Tagging: Flags known vulnerable VMs (Metasploitable 2, Stapler, Kioptrix, VulnHub) and generates critical security warnings if configured in bridged mode.
- **Relational Model & Schemas**:
  - `VirtualMachine`: Entity tracking hypervisor type, `.vmx` path, power state (`RUNNING`, `STOPPED`, `SUSPENDED`), hardware specs, adapter metadata, and network segment associations.
  - Pydantic v2 schemas: `VMResponse`, `VMRegisterRequest`, `VMDiscoverRequest`, `VMPowerRequest`, `NetworkAdapterInfo`, `VMDiscoveryResult`.
- **REST API Routes (`/api/v1/vms`)**:
  - `GET /api/v1/vms`: Lists all registered virtual machines with live adapter inspections.
  - `POST /api/v1/vms/discover`: Recursively scans host drives and imports discovered `.vmx` configurations (successfully verified with 13 real local VMs on host).
  - `POST /api/v1/vms/register`: Manual `.vmx` file path registration.
  - `POST /api/v1/vms/{id}/power`: Controls start, graceful shutdown, reset, and suspension with audit logging.
  - `POST /api/v1/vms/{id}/associate`: Links VM network cards to simulated CyberLab virtual bridges.
- **SOC VM Management UI (`frontend/src/components/vm/VMManagement.tsx`)**:
  - Comprehensive VM Fleet overview displaying live status cards for Metasploitable 2, Parrot OS, OPNsense, Stapler, Windows Server, etc.
  - Real-time power state indicators with glowing status badges.
  - Network Adapter Inspection panel displaying connection types (`custom vmnet1`), MAC addresses, and host-only isolation badges.
  - One-click "Discover Local VMs on Host" scanning button.
  - Dedicated power control buttons (Power On, Shut Down, Reset).
- **Automated Tests**:
  - `backend/tests/test_vm_integration.py` containing 4 tests verifying VMX parsing, bridged safety warnings, REST API power actions, and RBAC enforcement. Total test suite expanded to 23 passing tests.
- **Documentation**:
  - `documentation/VM_INTEGRATION.md`: Hypervisor integration guide, adapter models, discovered host machines, and security boundary policies.

---

## [Phase 2: Linux Network Simulation Engine] - 2026-11-24

### Added
- Linux Network Infrastructure Engine (`backend/app/network/`): `HostProtectionValidator`, `driver_interface.py`, `linux_driver.py`, `simulation_driver.py`, `manager.py`.
- Network Studio UI (`@xyflow/react`) with custom device nodes, drag-and-drop connections, properties inspector, and pre-flight safety preview modal.
- Models: `Topology`, `NetworkSegment`, `NetworkDevice`, `NetworkConnection`.
- REST API routes: `/api/v1/topologies`.
- Pytest suite expanded to 19 tests.
- Documentation: `documentation/NETWORK_ENGINE.md`.

---

## [Phase 1: Core Foundation] - 2026-11-24

### Added
- Architectural Documentation (`NETGUARDIAN_AUDIT.md`, `REUSE_MATRIX.md`, `CYBERLAB_ARCHITECTURE_COMPARISON.md`, `ARCHITECTURE.md`, `DEVELOPMENT_ROADMAP.md`, `DATABASE_DESIGN.md`, `API_DESIGN.md`, `SECURITY_ARCHITECTURE.md`).
- FastAPI modular backend with Pydantic settings, JWT authentication, and SQLite WAL database.
- RBAC roles: `super_admin`, `org_admin`, `soc_manager`, `soc_analyst`, `network_engineer`, `auditor`.
- Health probe (`/api/v1/health`) and immutable audit trail (`/api/v1/audit`).
- Next.js TypeScript frontend with Tailwind CSS and SOC dashboard.
- Pytest automated test suite (14 tests).
