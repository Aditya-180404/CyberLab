# CyberLab API Design

All CyberLab REST endpoints are versioned under the `/api/v1/` prefix.

---

## 1. Design Principles
1. **Predictable JSON Responses**: All endpoints return standard structured JSON envelopes with consistent status fields.
2. **Explicit Error Formats**: Errors include machine-readable error codes and human-readable messages.
3. **Stateless JWT Authentication**: Bearer tokens carry identity, role, and expiration claims.
4. **Least Privilege**: Endpoints enforce role checks at the route handler level via FastAPI dependencies.
5. **Audit Logging**: Sensitive mutating endpoints generate an immutable record in `audit_logs`.

---

## 2. Phase 1 Core Endpoints

### 2.1 Health & Diagnostics
- `GET /api/v1/health`
  - **Purpose**: System health check, database connectivity probe, resource utilization (CPU, memory, disk), platform telemetry.
  - **Auth**: Public or Operator.
  - **Response**:
    ```json
    {
      "status": "healthy",
      "timestamp": "2026-11-24T14:40:00Z",
      "version": "0.1.0",
      "database": "connected",
      "platform": {
        "os": "Linux",
        "kernel": "7.2.15+kali-amd64",
        "python": "3.14.10",
        "cpu_usage_pct": 4.2,
        "memory_usage_pct": 32.5,
        "disk_free_gb": 51.0
      }
    }
    ```

### 2.2 Authentication & Authorization (`/api/v1/auth`)
- `POST /api/v1/auth/login`
  - **Body**: `{"username": "admin", "password": "..."}`
  - **Response**: `{"access_token": "...", "token_type": "bearer", "user": {...}}`
- `GET /api/v1/auth/me`
  - **Header**: `Authorization: Bearer <token>`
  - **Response**: Current user profile, role, permissions.
- `POST /api/v1/auth/logout`
  - **Header**: `Authorization: Bearer <token>`
  - **Response**: Token invalidation / logout acknowledgment.

### 2.3 User Administration (`/api/v1/users`)
- `GET /api/v1/users`
  - **Auth**: SuperAdmin, OrgAdmin, SOCManager.
  - **Response**: Paginated list of registered users.
- `POST /api/v1/users`
  - **Auth**: SuperAdmin, OrgAdmin.
  - **Body**: New user specifications and role.

### 2.4 Audit Logs (`/api/v1/audit`)
- `GET /api/v1/audit`
  - **Auth**: SuperAdmin, Auditor, SOCManager.
  - **Query Params**: `limit`, `offset`, `action`, `resource_type`.
  - **Response**: Paginated immutable audit entries.

---

## 3. Future Roadmap Endpoints (Phases 2-12)
- `/api/v1/networks`: Network namespaces, bridges, veth pairs, VLANs.
- `/api/v1/vms`: VMware & QEMU virtual machine state and adapters.
- `/api/v1/agents`: Agent fleet registration, heartbeats, and telemetry.
- `/api/v1/events`: Normalized SIEM security event ingestion.
- `/api/v1/detections`: Detection rules, MITRE ATT&CK mappings, alerts.
- `/api/v1/incidents`: Incident lifecycle and evidence graphs.
- `/api/v1/digital-twin`: Graph topology and attack-path analysis.
- `/api/v1/simulations`: Safe attack simulation scenarios and runner.
- `/api/v1/validation`: Purple-team control validation test cases.
- `/api/v1/response`: SOAR actions, approvals, verification, and rollbacks.
