# CyberLab Changelog

All notable changes to the CyberLab platform are documented in this file.

---

## [Phase 11: Vulnerability Management & Asset Risk Scoring Engine] - 2026-11-24

### Added
- **Vulnerability Management & CVE Engine (`backend/app/vulnerability/`)**:
  - `VulnerabilityEngine` (`engine.py`): Ingests canonical CVE definitions with CVSS v3.1 scoring, affected products, and remediation advisories.
  - Automated Service-to-Vulnerability Matching: Correlates discovered listening ports, software banners, operating system versions, and vulnerable asset tags against known CVEs.
  - Dynamic Asset Risk Scoring: Continuously recalibrates composite asset posture risk (0–100) combining CVSS severity weights (Critical=+25, High=+15, Medium=+8), exposure modifiers (Public=+20, DMZ=+10), and asset criticality (Critical=+20, High=+10).
  - Remediation & Risk Reduction Tracking: Transitions findings through `OPEN` $\to$ `IN_REMEDIATION` $\to$ `MITIGATED` / `ACCEPTED_RISK`. Mitigating vulnerabilities instantly recalculates asset risk downward.
  - Pre-seeded Canonical CVE Catalog: Ingested definitions for `CVE-2011-2523` (vsftpd 2.3.4 backdoor), `CVE-2007-2447` (Samba MS-RPC), `CVE-2004-2687` (distcc RCE), `CVE-2008-0166` (Debian OpenSSH weak keys), `CVE-2007-6750` (Apache Slowloris), `CVE-2014-0160` (OpenSSL Heartbleed), and `CVE-2021-44228` (Log4Shell).
- **Relational Models & Schemas (`backend/app/models/vulnerability.py`, `backend/app/schemas/vulnerability.py`)**:
  - `Vulnerability`: Entity storing CVE ID, title, description, CVSS v3.1 score, severity, affected product/versions, port hints, and remediation advisory.
  - `AssetVulnerability`: Association table tracking findings per asset, detected services, status (`OPEN`, `IN_REMEDIATION`, `MITIGATED`, `ACCEPTED_RISK`), discovery/remediation timestamps, and notes.
  - Pydantic v2 schemas: `VulnerabilityResponse`, `AssetVulnerabilityItem`, `AssetVulnerabilitySummary`, `ScanAssetsRequest`, `ScanResultResponse`, `RemediateVulnerabilityRequest`, `VulnerabilityKPIs`.
- **REST API Endpoints (`backend/app/api/v1/vulnerability.py`)**:
  - `GET /api/v1/vulnerabilities`: Lists canonical CVEs with search and severity filtering.
  - `GET /api/v1/vulnerabilities/summary`: Per-asset vulnerability rollups across the fleet.
  - `POST /api/v1/vulnerabilities/scan`: Dispatches vulnerability scan on all assets or single asset.
  - `GET /api/v1/vulnerabilities/assets/{asset_id}`: Retrieves detailed vulnerability findings for an asset.
  - `POST /api/v1/vulnerabilities/remediate`: Updates remediation status and recalculates asset risk.
  - `GET /api/v1/vulnerabilities/kpis`: Fleet-wide vulnerability and remediation KPIs.
- **Frontend Vulnerability Management Workspace (`frontend/src/components/vulnerability/VulnerabilityManagement.tsx`)**:
  - KPI Bar: Asset Findings (Open count), Critical Severity (CVSS $\ge$ 9.0), Remediation Progress (%), Average CVSS Score.
  - "Run Fleet Vulnerability Scan" one-click action.
  - 3 Dedicated Sub-Views:
    1. *Asset Risk & Findings*: Fleet posture table with criticality and risk meters, plus Asset Findings Drawer showing detected CVEs and quick remediation buttons.
    2. *CVE Catalog & Advisories*: Searchable CVE library with severity filters, CVSS score pills, and remediation advisories.
    3. *Remediation Queue*: Active patch tracking console with status transition buttons ("Mark In-Progress", "Verify & Mitigate").
  - Navigation updated to platform version **`v0.10`** with `Vulnerabilities` marked **`ACTIVE`**.
- **Automated Tests (`backend/tests/test_vulnerability.py`)**:
  - 6 comprehensive tests verifying CVE seeding, service matching, asset vulnerability scanning, remediation state transitions, risk score reduction, and REST API endpoints.
  - Full backend test suite expanded to **65 passing tests**.
- **Documentation**:
  - `documentation/VULNERABILITY_MANAGEMENT.md`: Full technical specification of the CVSS v3.1 risk engine, service matching algorithm, and remediation lifecycle.

---

## [Phase 9-10: Purple-Team Validation Studio & Attack Simulation] - 2026-11-24

### Added
- **Purple-Team Validation & Simulation Engine (`backend/app/purple_team/`)**:
  - `PurpleTeamEngine` (`engine.py`): Continuous security control validation framework combining atomic attack simulations with SIEM/EDR detection verification.
  - Safe & Bounded Atomic Scenario Catalog:
    - `scen-t1082-sysinfo`: System Information Discovery (`T1082`, Discovery, benign `uname -a` baseline query).
    - `scen-t1033-userinfo`: Security Account Discovery (`T1033`, Discovery, benign `id && whoami` query).
    - `scen-t1110-brute-force`: SSH Authentication Brute Force (`T1110`, Credential Access, 6 rapid failed attempts verifying `RULE_AUTH_BRUTE_FORCE`).
    - `scen-t1548-sudo-abuse`: Sudo Rights Abuse (`T1548.003`, Privilege Escalation, unauthorized sudo invocation verifying `RULE_PRIVILEGE_ESCALATION_SUDO`).
    - `scen-t1003-shadow-dump`: /etc/shadow Canary Access (`T1003.008`, Credential Access, read probe verifying `RULE_CREDENTIAL_DUMPING_SHADOW`).
    - `scen-t1046-port-scan`: Network Service Recon (`T1046`, Discovery, multi-port SYN probe verifying `RULE_PORT_SCAN_RECON`).
    - `scen-t1059-shell-exec`: Suspicious Shell Command (`T1059.004`, Execution, base64 subshell probe verifying `RULE_SUSPICIOUS_REVERSE_SHELL`).
  - Closed-Loop SIEM Detection Verification: Correlates injected telemetry against generated `SecurityAlert` records within the test window to classify outcomes as `DETECTED` or `MISSED`.
  - Batch Purple-Team Campaigns (`run_campaign`): Automated execution across the atomic test suite measuring detection efficacy rates and Mean Time to Detect (MTTD).
  - MITRE ATT&CK Defensive Heatmap & Gap Analysis (`get_coverage_matrix`): Categorizes tested techniques into `COVERED` (100% detection), `PARTIAL`, or `GAP` (blind spot requiring SIEM rule creation).
- **Relational Models & Schemas (`backend/app/models/purple_team.py`, `backend/app/schemas/purple_team.py`)**:
  - `SimulationScenario`: Atomic test definitions mapped to MITRE tactics, safe payload types, and expected detection rules.
  - `SimulationExecution`: Execution records tracking target asset, dispatch timestamp, operator, execution logs, and telemetry.
  - `ValidationResult`: Verification records capturing detection status (`DETECTED`, `MISSED`, `BLOCKED`), matched alert ID, rule ID, and detection latency.
  - Pydantic v2 schemas: `SimulationScenarioResponse`, `ExecuteScenarioRequest`, `ValidationResultResponse`, `SimulationExecutionResponse`, `RunCampaignRequest`, `RunCampaignResponse`, `MitreCoverageResponse`, `PurpleTeamKPIs`.
- **REST API Endpoints (`backend/app/api/v1/purple_team.py`)**:
  - `GET /api/v1/purple-team/scenarios`: Lists atomic scenarios with optional tactic filter.
  - `POST /api/v1/purple-team/execute`: Dispatches an atomic test against an authorized asset.
  - `POST /api/v1/purple-team/run-campaign`: Executes an automated purple-team validation campaign.
  - `GET /api/v1/purple-team/executions`: Historical execution log and detection results.
  - `GET /api/v1/purple-team/coverage`: MITRE ATT&CK defensive detection coverage matrix.
  - `GET /api/v1/purple-team/kpis`: Real-time efficacy rate, MTTD, and by-tactic statistics.
- **Frontend Purple-Team Studio (`frontend/src/components/purple_team/PurpleTeamStudio.tsx`)**:
  - KPI Header Bar: Simulations Run, Detection Efficacy Rate (%), Mean Time to Detect (s), Coverage Gaps Identified.
  - 3 Interactive Sub-Views:
    1. *Atomic Test Catalog*: Tactic filter pills, target asset selector, command preview blocks, expected SIEM rule tags, and "Execute Atomic Test" triggers.
    2. *Validation Runs & Log*: Chronological execution table with `DETECTED` vs `MISSED` badges, latency metrics, and run inspection drawer with terminal logs.
    3. *MITRE ATT&CK Defensive Heatmap & Gaps*: Multi-column matrix showing covered techniques vs detection blind spots needing rule authoring.
  - Sidebar updated to platform version **`v0.9`** with `Purple-Team Studio` marked **`ACTIVE`**.
- **Automated Tests (`backend/tests/test_purple_team.py`)**:
  - 7 comprehensive tests verifying scenario catalog seeding, detected execution, missed gap detection, automated campaign execution, MITRE coverage matrix, KPIs, and REST API endpoints.
  - Full backend test suite expanded to **59 passing tests**.
- **Documentation**:
  - `documentation/PURPLE_TEAM.md`: Comprehensive specification of the purple-team validation framework, atomic scenarios, efficacy formulations, and API endpoints.

---

## [Phase 8: Digital Twin & Attack-Path Analysis Engine] - 2026-11-24

### Added
- **Digital Twin & Network Graph Engine (`backend/app/digital_twin/`)**:
  - `DigitalTwinGraphEngine` (`graph_engine.py`): Real-time NetworkX directed multigraph (`DiGraph`) modeling the enterprise and lab cybersecurity topology.
  - Multi-Zone Architecture Ingestion:
    - `EXTERNAL / WAN`: Threat actor entrypoints (e.g. `node-adversary-ext-01`, 198.51.100.50).
    - `TRANSIT_ROUTER / PERIMETER`: Edge firewalls and core transit routers (`node-perimeter-fw-01`, `node-core-router-01`).
    - `DMZ`: Public services (`node-dmz-web-proxy-01`, 10.10.10.15).
    - `INTERNAL LAN`: Discovered VMware virtual machines (`Metasploitable2-Linux`, `Parrot`, `Opensence`), Linux agents, and simulated endpoints.
    - `SECURE_VAULT`: Crown Jewel assets (`node-crown-jewel-db-vault`, 10.10.30.50, PostgreSQL/MySQL credentials and secrets).
  - Telemetry & State Synchronization: Dynamically reads active SIEM incidents (`SecurityIncident`) and high-severity detections (`SecurityAlert`) to mark compromised nodes in real time.
- **Attack-Path Discovery & MITRE ATT&CK Mapping**:
  - Multi-hop traversal calculation: Identifies all viable attack paths between untrusted ingress nodes and critical internal assets using NetworkX `all_simple_paths` and Dijkstra shortest path.
  - Step-by-step MITRE ATT&CK technique mapping:
    - Ingress: `T1190` (*Exploit Public-Facing Application*)
    - Evasion: `T1562.001` (*Disable or Evade Security Tools*)
    - Lateral Movement: `T1021.004` (*SSH Remote Services*), `T1046` (*Network Service Discovery*)
    - Privilege Escalation: `T1068` (*Exploitation for Privilege Escalation*), `T1548.003` (*Sudo and Sudo Caching*)
    - Target Impact: `T1003.008` (*/etc/shadow & Credential Vault Access*)
  - Cumulative path risk scoring (0–100%) and viability classification (`HIGH`, `MEDIUM`, `LOW`).
- **Blast-Radius Quantification**:
  - Downstream reachability via single-source shortest path traversal (`nx.single_source_shortest_path_length`).
  - Weighted blast score formula (0–100) factoring reachable asset criticality (`CRITICAL`=40, `HIGH`=25, `MEDIUM/LOW`=10) and proximity distance.
  - Automated containment recommendations integrated with SOAR playbooks (`playbook-host-quarantine`, `playbook-block-attacker-ip`).
- **Defensive Choke-Point Optimization**:
  - NetworkX **Betweenness Centrality** calculation ranking transit nodes and cut vertices.
  - Quantifies paths intercepted % and critical assets shielded.
  - Concrete defensive suggestions (`ENFORCE_FIREWALL_FILTER`, `DEPLOY_AGENT_EDR`).
- **Dynamic What-If Compromise Simulation**:
  - In-memory simulation controls (`simulate_compromise`, `reset_simulation`) enabling operators to test hypothetical compromise scenarios and re-evaluate attack paths and blast radius in real time.
- **REST API Endpoints (`backend/app/api/v1/digital_twin.py`)**:
  - `GET /api/v1/digital-twin/graph`: Full topological graph nodes and edges.
  - `POST /api/v1/digital-twin/attack-paths`: Discovers ranked attack paths.
  - `GET /api/v1/digital-twin/blast-radius/{asset_id}`: Evaluates downstream impact.
  - `GET /api/v1/digital-twin/choke-points`: Identifies optimal defensive bottlenecks.
  - `POST /api/v1/digital-twin/simulate-compromise`: Toggles transient compromise for what-if modeling.
  - `POST /api/v1/digital-twin/reset-simulation`: Clears all transient compromise states.
- **Frontend Digital Twin Console (`frontend/src/components/digital_twin/DigitalTwinView.tsx`)**:
  - KPI Bar: Total Nodes, Directed Edges, Compromised Entities, Crown Jewels, Avg Risk, Choke Points.
  - 4 Interactive Sub-Views:
    1. *Attack Path Discovery*: Interactive source/target selectors, viable path vector list, and step-by-step MITRE ATT&CK progression cards.
    2. *Blast Radius Analyzer*: Selected asset blast score gauge (0–100%), downstream reachability breakdown, and target asset table.
    3. *Defensive Choke Points*: Centrality-ranked cards with paths cut %, critical assets shielded, and action pills.
    4. *Topological Twin Map*: Tiered architectural zone columns (EXTERNAL, TRANSIT, DMZ, INTERNAL, SECURE VAULT), live node status indicators, and node inspector drawer with "Simulate Compromise" toggle.
  - Navigation updated to `v0.8` with `Digital Twin` set to `ACTIVE`.
- **Automated Tests (`backend/tests/test_digital_twin.py`)**:
  - 7 comprehensive tests verifying graph construction, attack path discovery, error handling, blast radius, choke points, what-if simulation, and REST API endpoints.
  - Full backend test suite expanded to **52 passing tests**.
- **Documentation**:
  - `documentation/DIGITAL_TWIN.md`: Complete technical specification of the Digital Twin engine, mathematical formulations, MITRE mappings, and API endpoints.

---

## [Phase 7: Security Orchestration, Automation & Response (SOAR)] - 2026-11-24

### Added
- **SOAR Engine & Automated Containment (`backend/app/soar/`)**:
  - `SOAREngine` (`engine.py`): Orchestrates automated and human-approved containment workflows across agents, virtual machines, and simulated network nodes.
  - Action Types supported:
    - `ISOLATE_HOST`: Quarantines compromised endpoint via EDR agent and virtual bridge/nftables filter.
    - `RESTORE_HOST`: Re-opens network traffic and restores normal operating policy.
    - `BLOCK_IP`: Drops ingress/egress from malicious attacker IP across perimeter filters.
    - `UNBLOCK_IP`: Removes perimeter firewall drop rule.
    - `SUSPEND_VM`: Suspends VMware Workstation guest via hypervisor CLI to freeze RAM state for forensics.
    - `REVOKE_CREDENTIALS`: Scrambles authentication token hashes and disconnects compromised rogue agents.
  - Human-in-the-Loop (HITL) Authorization Gates: High-impact disruptive operations queue in `PENDING_APPROVAL` status requiring explicit SOC Analyst / Admin signoff with audit logging.
  - Post-Execution Automated Verification: Verifies that target entities successfully transitioned into the expected state (e.g. `AgentStatus.ISOLATED`).
  - Non-Destructive State Rollback Engine: Every containment action can be cleanly reversed with a single click, restoring endpoints and powering suspended virtual machines back on.
  - Default Playbook Library: Pre-configured playbooks for Endpoint Quarantine, Malicious IP Block, VM Emergency Suspend, and Credential Revocation.
- **Relational Models & Schemas (`backend/app/models/soar.py`, `backend/app/schemas/soar.py`)**:
  - `SOARPlaybook`: Entity tracking playbook name, trigger events, action types, and approval policy.
  - `SOARAction`: Entity tracking action execution status, target entities, requesting users, approvers, verification details, and rollback states.
  - Pydantic v2 schemas: `SOARPlaybookResponse`, `SOARActionCreateRequest`, `SOARActionResponse`, `SOARApprovalDecisionRequest`, `SOARKPIs`.
- **REST API Endpoints (`backend/app/api/v1/soar.py`)**:
  - `GET /api/v1/soar/playbooks`: Lists available playbooks, auto-seeding defaults if needed.
  - `POST /api/v1/soar/playbooks/{id}/execute`: Triggers playbook execution, evaluating approval gates.
  - `GET /api/v1/soar/actions`: Lists action history with execution and verification details.
  - `POST /api/v1/soar/actions/{id}/approve`: Authorizes and executes pending containment action.
  - `POST /api/v1/soar/actions/{id}/reject`: Rejects a pending containment action with an audit reason.
  - `POST /api/v1/soar/actions/{id}/rollback`: Reverses an executed containment action.
  - `GET /api/v1/soar/kpis`: Real-time response action metrics and pending queue count.
- **Frontend Incident Response & SOAR Workspace (`frontend/src/components/soar/IncidentResponseSOAR.tsx`)**:
  - Fleet KPI Cards: Total Response Actions, Pending Approvals (with animated alert pulse), Verified Actions, and Rolled-Back Actions.
  - Human-in-the-Loop Authorization Queue: Interactive review panel allowing analysts to inspect pending actions and click "Authorize & Execute" or "Reject".
  - Automated Playbook Catalog: Card grid displaying available containment playbooks with approval badges and one-click manual execution modal.
  - Action History & Rollback Console: Complete audit log of executed actions with verification badges and one-click "Rollback Action" button.
- **Automated Tests (`backend/tests/test_soar.py`)**:
  - 6 comprehensive tests verifying playbook listing, approval gate enforcement, automated execution without approval, rejection with audit reason, rollback lifecycle, and SOAR KPIs.
  - Full backend test suite expanded to 45 passing tests.
- **Documentation**:
  - `documentation/SOAR_ENGINE.md`: Full architectural specification of the SOAR pipeline, playbooks, approval governance, and rollback mechanics.

---

## [Phase 6: SIEM, Detection Engine & MITRE ATT&CK Mapping] - 2026-11-24

### Added
- **SIEM & Detection Engine (`backend/app/siem/`)**:
  - `SIEMEngine` (`engine.py`): Ingests, normalizes, and inspects real-time security events across distributed agents, VMware virtual machines, and simulated network nodes.
  - Stateful Rule-Based Detection Engine (`rules.py`): Real-time behavioral detection rules mapped to MITRE ATT&CK techniques:
    - `RULE_AUTH_BRUTE_FORCE` (T1110: Brute Force)
    - `RULE_PRIVILEGE_ESCALATION_SUDO` (T1548.003: Sudo and Sudo Caching)
    - `RULE_CREDENTIAL_DUMPING_SHADOW` (T1003.008: /etc/passwd and /etc/shadow)
    - `RULE_SUSPICIOUS_REVERSE_SHELL` (T1059.004: Unix Shell)
    - `RULE_PORT_SCAN_RECON` (T1046: Network Service Discovery)
  - Multi-Stage Incident Correlation Engine: Automatically detects correlated multi-vector attacks against a target host, linking disparate alerts into unified `SecurityIncident` records with root cause analysis.
  - Time-Windowed Alert Deduplication: Aggregates repetitive alert firings into single alerts with `evidence_count` counters.
  - Synthetic Attack Simulator: Injects multi-stage attack scenarios (`brute_force`, `privilege_escalation`, `credential_dumping`, `reverse_shell`) for automated purple-team validation.
- **Relational Models & Schemas (`backend/app/models/siem.py`, `backend/app/schemas/siem.py`)**:
  - `SecurityEvent`: Normalized security event table conforming to ECS event taxonomy.
  - `SecurityAlert`: Rule detection alert table with MITRE tactic and technique tags.
  - `SecurityIncident`: Correlated multi-stage security incident table.
  - Pydantic v2 schemas: `SecurityEventCreate`, `SecurityEventResponse`, `SecurityAlertResponse`, `SecurityIncidentResponse`, `MitreMatrixSummary`, `SIEMKPIs`, `AttackSimulationRequest`.
- **REST API Endpoints (`backend/app/api/v1/siem.py`)**:
  - `GET /api/v1/siem/events`: Stream normalized events with multi-criteria filtering.
  - `POST /api/v1/siem/events`: Real-time event ingestion and detection evaluation.
  - `GET /api/v1/siem/alerts`: Aggregated security alerts stream.
  - `GET /api/v1/siem/incidents`: Correlated multi-stage security incidents.
  - `GET /api/v1/siem/mitre`: Interactive MITRE ATT&CK matrix heatmap with active hit counts.
  - `GET /api/v1/siem/kpis`: Real-time SIEM counters and category breakdown.
  - `POST /api/v1/siem/simulate`: Offensive attack simulation execution with audit logging.
- **SOC SIEM Dashboard (`frontend/src/components/siem/SIEMDashboard.tsx`)**:
  - Fleet KPI cards: Ingested Events volume, Open Security Alerts, Correlated Incidents, and Active MITRE ATT&CK Techniques.
  - Interactive MITRE ATT&CK Matrix: Visual heatmap spanning 9 Enterprise Tactics with glowing threat detection indicators.
  - Correlated Incidents & Alerts View: Multi-stage incident summaries with MITRE tactic chains.
  - Live Event Stream: Console-style log viewer with severity badges, category pills, and search.
  - One-Click Attack Simulation Modal: Instant injection of attack scenarios against targets like Metasploitable 2.
- **Automated Tests (`backend/tests/test_siem.py`)**:
  - 5 tests covering event ingestion, brute force detection, incident correlation across multiple stages, attack simulation, and MITRE matrix telemetry.
  - Full backend test suite expanded to 39 passing tests.
- **Documentation**:
  - `documentation/SIEM_ARCHITECTURE.md`: Complete specification of SIEM architecture, rule engine, correlation algorithm, and MITRE ATT&CK mapping.

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
