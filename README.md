# CyberLab

> **Hybrid Cybersecurity Infrastructure, Network Simulation, Distributed Endpoint Security, SIEM, SOC, and Purple-Team Platform**

[![Platform: Linux](https://img.shields.io/badge/Platform-Linux-blue.svg)](https://www.kernel.org)
[![Backend: FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![Frontend: Next.js](https://img.shields.io/badge/Frontend-Next.js-black.svg)](https://nextjs.org)
[![Language: TypeScript](https://img.shields.io/badge/Language-TypeScript-3178C6.svg)](https://www.typescriptlang.org)
[![Language: Python](https://img.shields.io/badge/Language-Python%203.10+-3776AB.svg)](https://www.python.org)
[![Security: RBAC](https://img.shields.io/badge/Security-RBAC%20Enabled-green.svg)](#)

---

## 1. Product Overview

**CyberLab** is a modular, extensible, and security-focused hybrid platform designed for cybersecurity laboratories, training environments, security operations centers (SOCs), and enterprise research facilities.

It combines capabilities traditionally fragmented across multiple disconnected systems:
- **Network Simulation & Infrastructure**: Linux network namespaces, veth pairs, Linux bridges, nftables, and real VMware Workstation virtual machines.
- **Distributed Endpoint Security (EDR)**: Distributed Linux agents providing hardware inventory, process monitoring, authentication auditing, File Integrity Monitoring (FIM), and controlled network isolation.
- **SIEM & Security Intelligence**: Unified security event normalization, MITRE ATT&CK tactical mapping, rule-based detection, multi-host correlation, and evidence-based root-cause analysis (RCA).
- **Digital Twin & Attack Paths**: Topological graph modeling (NetworkX), blast-radius calculation, reachability analysis, and what-if containment simulation.
- **Attack Simulation & Purple-Team Validation**: Bounded, controlled attack simulation scenarios verifying that detection rules and automated defenses perform as expected.
- **SOAR & Response Automation**: Multi-stage approval-gated containment, firewall policy automation, verification probes, and verified rollback.

---

## 2. Architecture & Technology Stack

| Tier | Component | Technology |
|---|---|---|
| **Frontend** | Framework | Next.js (App Router), React, TypeScript |
| | Styling | Tailwind CSS |
| | Icons | Lucide React |
| | Topology | React Flow (`@xyflow/react`) |
| **Backend** | API Engine | Python FastAPI |
| | Validation | Pydantic v2 |
| | ORM | SQLAlchemy 2.0 |
| | Database | SQLite initially (PostgreSQL-ready schema) |
| | Graph Engine | NetworkX |
| **Infrastructure** | Network Virtualization | Linux namespaces (`ip netns`), `veth`, Linux bridges, `nftables` |
| | VM Integration | VMware Workstation (`vmrun`), QEMU/KVM (`virsh` future) |
| **Agent** | Target OS | Linux (Ubuntu, Debian, Kali, RHEL) |
| | Runtime | Python 3 |

---

## 3. Directory Structure

```
CyberLab/
├── backend/                      # Python FastAPI Backend
│   ├── app/
│   │   ├── api/v1/              # API Route Handlers (auth, health, users, audit, etc.)
│   │   ├── core/                # Config, Security, JWT, Dependencies
│   │   ├── database/            # Database Engine, Session, Seeding
│   │   ├── middleware/          # Security Headers, Logging
│   │   ├── models/              # SQLAlchemy 2.0 Declarative Models
│   │   └── schemas/             # Pydantic Schemas
│   ├── tests/                   # Automated Pytest Suite
│   └── requirements.txt         # Backend Dependencies
├── frontend/                     # Next.js TypeScript Frontend
│   ├── src/
│   │   ├── app/                 # Next.js App Router Pages
│   │   ├── components/          # Reusable UI & SOC Components
│   │   └── lib/                 # API Client & Utility Functions
│   ├── package.json             # Frontend Dependencies
│   └── tailwind.config.ts       # Tailwind CSS Configuration
├── documentation/                # Architectural & Technical Docs
│   ├── ARCHITECTURE.md          # Multi-tier System Architecture
│   ├── DEVELOPMENT_ROADMAP.md   # 12-Phase Incremental Plan
│   ├── DATABASE_DESIGN.md       # Relational Database Models
│   ├── API_DESIGN.md            # REST API Specification
│   ├── SECURITY_ARCHITECTURE.md # Security Controls & RBAC
│   ├── NETGUARDIAN_AUDIT.md     # Reference Audit Report
│   ├── REUSE_MATRIX.md          # Component Adaptation Matrix
│   ├── CYBERLAB_ARCHITECTURE_COMPARISON.md # Architectural Divergence
│   └── CHANGELOG.md             # Project Release Notes
└── README.md
```

---

## 4. Phase 1 Quickstart

### 4.1 Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest -v
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4.2 Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Open your browser at `http://localhost:3000` to access the CyberLab SOC Dashboard.
