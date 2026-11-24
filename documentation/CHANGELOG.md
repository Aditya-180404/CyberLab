# CyberLab Changelog

All notable changes to the CyberLab platform are documented in this file.

---

## [Phase 2: Linux Network Simulation Engine] - 2026-11-24

### Added
- **Linux Network Infrastructure Engine (`backend/app/network/`)**:
  - `safety.py`: `HostProtectionValidator` enforcing strict boundary isolation; prevents any mutation of physical interfaces (`wlan0`, `eth0`, `lo`) and host default gateway.
  - `driver_interface.py`: Abstract `NetworkDriver` contract for virtual networking.
  - `linux_driver.py`: `LinuxKernelDriver` managing real `ip netns`, `veth`, `bridge`, `vlan`, and `nftables` via allowlisted commands.
  - `simulation_driver.py`: `SimulationDriver` providing sandboxed in-memory network modeling, CIDR validation, IP conflict detection, and packet routing metrics.
  - `manager.py`: `NetworkEngineManager` orchestrating pre-flight safety previews, sequential deployment, and graceful reverse teardown.
- **Relational Models & Schemas**:
  - `Topology`: Visual network design persistence with React Flow canvas coordinates.
  - `NetworkSegment`: Subnets, virtual bridges (`cl-br-*`), and 802.1Q VLAN IDs.
  - `NetworkDevice`: Virtual routers, switches, firewalls, and Linux endpoints mapped to isolated namespaces (`cl-ns-*`).
  - `NetworkConnection`: Virtual Ethernet cable pairs (`cl-ep-*` <-> `cl-brp-*`).
- **REST API Routes (`/api/v1/topologies`)**:
  - Topology CRUD with RBAC enforcement (`NetworkEngineer`, `Admin`).
  - `GET /api/v1/topologies/{id}/preview`: Pre-flight safety check and resource preview.
  - `POST /api/v1/topologies/{id}/deploy`: Deploys isolated virtual bridges and namespaces.
  - `POST /api/v1/topologies/{id}/teardown`: Safely tears down and deletes virtual resources.
- **Interactive Network Studio (Frontend)**:
  - React Flow (`@xyflow/react`) canvas editor under `frontend/src/components/network/NetworkStudio.tsx`.
  - Custom dark-theme device node component (`CustomDeviceNode.tsx`) with status indicators, IP labels, and drag-and-drop connection handles.
  - Device palette for adding Routers, Bridges, Firewalls, Servers, and Endpoints.
  - Real-time properties inspector for editing hostnames, IP CIDR, and VLAN IDs.
  - Pre-flight safety preview modal before real deployment.
  - One-click Simulation Deployment & Teardown controls with glowing state badges.
- **Documentation**:
  - `documentation/NETWORK_ENGINE.md`: Full architectural reference for Linux network namespaces, veth pairs, bridges, VLANs, and safety constraints.

---

## [Phase 1: Core Foundation] - 2026-11-24

### Added
- Architectural Documentation (`NETGUARDIAN_AUDIT.md`, `REUSE_MATRIX.md`, `CYBERLAB_ARCHITECTURE_COMPARISON.md`, `ARCHITECTURE.md`, `DEVELOPMENT_ROADMAP.md`, `DATABASE_DESIGN.md`, `API_DESIGN.md`, `SECURITY_ARCHITECTURE.md`).
- FastAPI modular backend with Pydantic settings, JWT authentication, and SQLite WAL database.
- RBAC roles: `super_admin`, `org_admin`, `soc_manager`, `soc_analyst`, `network_engineer`, `auditor`.
- Health probe (`/api/v1/health`) and immutable audit trail (`/api/v1/audit`).
- Next.js TypeScript frontend with Tailwind CSS and SOC dashboard.
- Pytest automated test suite.
