# CyberLab Platform Architecture

## 1. System Vision & Overview

CyberLab is a modular, extensible, and security-focused hybrid platform uniting:
1. **Network Simulation & Infrastructure Control** (Linux network namespaces, veth, bridges, nftables, VMware Workstation).
2. **Distributed Endpoint Security (EDR)** (Multi-host Linux telemetry, inventory, process, auth, FIM, and isolation).
3. **SIEM & Security Intelligence** (Normalized event ingestion, MITRE ATT&CK correlation, and root-cause analysis).
4. **Digital Twin & Attack-Path Modeling** (NetworkX graph topology, blast radius, reachability, and what-if analysis).
5. **Attack Simulation & Purple-Team Validation** (Authorized, bounded testing of security controls).
6. **SOAR & Response Automation** (Approval-gated containment, firewall policy management, verification, and rollback).

---

## 2. Multi-Tier System Topology

```
+-----------------------------------------------------------------------------------------+
|                                    USER INTERFACE                                       |
| Next.js 14+ | React 18 | TypeScript | Tailwind CSS | React Flow (@xyflow/react) | Lucide   |
+-----------------------------------------------------------------------------------------+
                                             │  REST API / WebSockets
+--------------------------------------------▼--------------------------------------------+
|                                CYBERLAB BACKEND CORE                                    |
| FastAPI | Python 3.10+ | Pydantic v2 | SQLAlchemy 2.0 (SQLite -> Postgres) | NetworkX   |
|                                                                                         |
|  [Auth & RBAC]         [Asset & Inventory]      [Simulation Engine]                     |
|  [SIEM & Correlation]  [Digital Twin Engine]    [Incident Management]                   |
|  [SOAR Orchestrator]   [Agent Fleet Manager]    [Purple-Team Validator]                 |
|  [Audit Logging]       [VM Integration Adapter] [Vulnerability Ingestion]               |
+-----------------------------------------------------------------------------------------+
               │                                   │                           │
  Privileged Helper (Restricted)       mTLS / TLS Heartbeat          Hypervisor Adapter
               │                                   │                           │
+--------------▼---------------+     +-------------▼-------------+     +-------▼----------+
|  LINUX KERNEL NETWORKING     |     | DISTRIBUTED LINUX AGENTS  |     | VIRTUAL MACHINES |
| - Network Namespaces (netns) |     | - Host & Network Inventory|     | - VMware CLI     |
| - Virtual Ethernet (veth)    |     | - Process & Parent Trees  |     | - Network Cards  |
| - Linux Bridges (br0)        |     | - Auth Logs & Sudo Events |     | - Power States   |
| - VLAN-aware Switching       |     | - File Integrity (FIM)    |     | - Snapshot Sync  |
| - nftables Packet Filtering  |     | - Network Sockets / Conns |     | - QEMU/KVM       |
|                              |     | - Quarantine / Isolation  |     |   (Future)       |
+------------------------------+     +---------------------------+     +------------------+
```

---

## 3. Module Responsibilities

### 3.1 Frontend (`frontend/`)
- **Technology**: Next.js (App Router), React, TypeScript, Tailwind CSS, `@xyflow/react`, `lucide-react`.
- **Security Boundaries**: Purely client-side presentation layer. Never issues direct shell commands. All operations pass through authenticated REST endpoints (`/api/v1/*`) or secure WebSocket channels.

### 3.2 Backend (`backend/`)
- **Technology**: FastAPI, SQLAlchemy 2.0, Pydantic 2, SQLite (dev) / PostgreSQL (prod ready).
- **Modularity**: Domain-driven directory organization:
  - `app/api/v1/`: HTTP routers segmented by domain (auth, health, users, agents, networks, incidents, etc.).
  - `app/core/`: Configuration, security hashing, JWT, dependency injection, exception handlers.
  - `app/models/`: SQLAlchemy declarative database tables.
  - `app/schemas/`: Pydantic validation schemas.
  - `app/services/`: Core business logic decoupled from API endpoints.
  - `app/engines/`: Complex algorithmic modules (Correlation, RCA, Digital Twin, Purple-Team).

### 3.3 Linux Network Infrastructure Engine
- Manages isolated Linux network namespaces (`ip netns`), creating clean virtual network topologies without disrupting host connectivity.
- Enforces strict safety rules: physical and Wi-Fi interfaces (`wlan0`, `eth0`, default gateway) are strictly excluded from mutation.

### 3.4 Distributed Linux Agent Platform
- Lightweight, standalone Python client running on managed target nodes.
- Communicates out-of-band via encrypted JSON over WebSockets/HTTPS with the central server.
- Supports offline policy caching: if connection is severed, local protection policies continue to run.

---

## 4. Phase 1 Implementation Scope

Phase 1 establishes the operational core foundation:
1. Complete directory structure for backend, frontend, agents, and documentation.
2. FastAPI backend with configuration management, SQLite database integration, JWT authentication, user roles, security headers, structured logging, and health endpoints.
3. Next.js TypeScript frontend with Tailwind CSS, Lucide icons, responsive navigation, and dark SOC theme.
4. Comprehensive automated unit and API test suite.
5. Verifiable local execution verifying backend-to-frontend communication.
