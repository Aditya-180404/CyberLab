# CyberLab v1.0.0 — Known Architectural Limitations & Boundaries

**Audit Status**: Verified & Cataloged  
**Platform Version**: v1.0.0  
**Auditor Roles**: Principal Security Auditor, Senior Software Architect  

This document provides a transparent, evidence-based catalog of all known limitations, architectural boundaries, and simulation fallbacks in CyberLab v1.0.0.

---

## 1. Network Simulation Engine (Phase 2)
- **Driver Decoupling in API Server**:
  `NetworkEngineManager` in `backend/app/network/manager.py` unconditionally initializes `SimulationDriver()`. While `LinuxKernelDriver` is fully implemented and tested with mock fixtures, there is currently no runtime configuration flag (e.g. `NETWORK_ENGINE_DRIVER=kernel`) in `Settings` to wire `LinuxKernelDriver` to the FastAPI API router.
- **Root / Privilege Boundaries**:
  Real Linux kernel namespaces (`ip netns`), software bridges, and `nftables` tables require root or `CAP_NET_ADMIN` capabilities, which are intentionally bypassed during web server execution for host security.

## 2. Real Virtual Machine Integration (Phase 3)
- **Logical Segment Binding**:
  Associating a virtual machine with a network segment via `POST /api/v1/vms/{id}/associate` updates the database foreign key (`vm.attached_segment_id = segment_id`). It does **not** rewrite `.vmx` adapter configurations or dynamically plumb VMware vnet interfaces to Linux bridges in-place. This preserves VM file integrity but represents a logical topology association rather than an active hypervisor network re-binding.
- **Hypervisor Binary Dependency**:
  `VMwareWorkstationAdapter` requires `/usr/bin/vmrun` to be present on the host filesystem. If VMware Workstation is not installed, VM power actions fail with runtime errors.

## 3. Distributed Linux Agent (Phase 4)
- **Unauthenticated Registration**:
  The `POST /api/v1/agents/register` endpoint does not require an enrollment token, administrative authorization, or pre-shared key.
- **Faux Host Isolation**:
  The agent's `apply_isolation()` method sets `self.is_isolated = True` and writes to its local JSON configuration file. It does **not** execute kernel `nftables` or `iptables` drop rules.
- **Unparsed Authentication Logs**:
  The agent's telemetry payload sends an empty list for `auth_events: []`. It does not tail `/var/log/auth.log` or `/var/log/secure`.
- **Plaintext HTTP Default**:
  Agent communication defaults to unencrypted HTTP (`http://127.0.0.1:8000`) with no TLS certificate validation or certificate fingerprint pinning.

## 4. SIEM & Detection Engine (Phase 6)
- **Substring-Based Rule Evaluation**:
  Detection rules (e.g. `ReverseShellRule`, `SudoPrivilegeEscalationRule`, `ReconnaissanceRule`) evaluate substring matches on the event `message` text (e.g., checking for `/bin/bash -i` or `not in sudoers`). They do not analyze kernel auditd syscalls or network packet byte streams, which can lead to false positives on benign text matching.

## 5. SOAR & Incident Response (Phase 7)
- **Simulated IP Block Actions**:
  `ActionType.BLOCK_IP` and `ActionType.UNBLOCK_IP` update database records and set `verified = True` in the execution output log, but **do not execute any real firewall commands**.

## 6. Digital Twin & Attack Paths (Phase 8)
- **Synthetic Topological Anchors**:
  If the active database lacks WAN entry points, perimeter firewalls, or crown-jewel databases, `DigitalTwinGraphEngine._ensure_enterprise_twin_topology` automatically injects synthetic anchor nodes (`node-adversary-ext-01`, `node-perimeter-fw-01`, `node-core-router-01`, `node-internal-lan-01`, `node-secure-db-01`) into the NetworkX graph to allow end-to-end path calculations.

## 7. Purple-Team Validation Studio (Phase 9–10)
- **Synthetic Telemetry Ingestion**:
  Executing an atomic simulation scenario does not dispatch live packets or SSH connection attempts across the physical network. Instead, it generates benign, controlled `SecurityEventCreate` records directly into the central SIEM pipeline to validate detection rule triggering and measure latency in a closed loop.

## 8. Vulnerability Management (Phase 11)
- **Port-Only Matching Risk**:
  `VulnerabilityEngine.scan_asset` matches CVEs based on open listening port numbers (`svc_port == cve.port_hint`) without checking software banners or version strings. This creates false-positive matches (e.g., modern OpenSSH on port 22 flagged for a 2008 weak-keys vulnerability).

## 9. Enterprise Compliance Engine (Phase 12)
- **Static Compliance Scoring**:
  Certain compliance control items (such as `PR.AC-02` RBAC and `PR.DS-05` FIM) report static 100% or 95% scores and pre-written evidence strings without dynamically querying telemetry metrics.

## 10. PostgreSQL & Packaging (Phase 12)
- **Missing Requirements**:
  `networkx`, `psycopg2-binary`, and `alembic` are omitted from `backend/requirements.txt`.
- **Schema Lifecycle**:
  Database initialization relies on `Base.metadata.create_all`, which lacks schema alteration and migration rollback capabilities provided by Alembic.
