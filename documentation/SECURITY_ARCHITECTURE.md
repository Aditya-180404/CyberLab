# CyberLab Security Architecture & Hardening Guide

## 1. Security Architecture Principles

CyberLab is a security platform; it must adhere to the highest engineering security standards.

### 1.1 Defense in Depth & Separation of Privilege
- **Non-Root Execution**: The FastAPI backend runs as an unprivileged service user (`ghost` in development, dedicated service user in production).
- **Narrowly Scoped Privileged Operations**: Network-level commands requiring root (e.g. `ip netns add`, `nft add rule`) are strictly encapsulated into dedicated helper scripts with validated, allowlisted arguments. The web server never executes arbitrary user-supplied shell commands.
- **Protected Interface Exclusions**: Core host interfaces (e.g., `wlan0`, `eth0`, physical interfaces, host default gateway) are strictly excluded from mutation.

### 1.2 Authentication & Cryptography
- **Password Storage**: Modern cryptographic password hashing using Argon2 or PBKDF2/Bcrypt with random salting.
- **Session Tokens**: Cryptographically signed JSON Web Tokens (JWT) using HMAC-SHA256 with cryptographically generated random secrets (no hardcoded secrets).
- **Token Claims**: Strict validation of `exp` (expiration), `iss` (issuer), `aud` (audience), and `sub` (subject).

### 1.3 Role-Based Access Control (RBAC)
Role hierarchy enforced on backend API endpoints:
1. **Super Administrator**: Complete system administration, organization creation, system configuration.
2. **Organization Administrator**: Manages users, sites, and assets within their organization.
3. **SOC Manager**: Approves response actions, manages detection rules, and oversees incidents.
4. **SOC Analyst**: Investigates alerts, reviews telemetry, drafts incident notes, requests containment.
5. **Network Engineer**: Designs topologies, connects virtual interfaces, configures simulation routes.
6. **Auditor**: Read-only access to audit logs, compliance evidence, and security reports.

### 1.4 API Hardening & Middleware
- **Security Headers**: All HTTP responses include:
  - `Content-Security-Policy`: Restricts scripts and styles.
  - `X-Content-Type-Options: nosniff`: Prevents MIME-confusion attacks.
  - `X-Frame-Options: DENY`: Prevents clickjacking.
  - `Strict-Transport-Security`: Enforces TLS when in production.
  - `Referrer-Policy: strict-origin-when-cross-origin`.
- **CORS Protection**: Restricted to explicitly configured origins (e.g. `http://localhost:3000` during development).
- **Input Validation**: Strict schema enforcement using Pydantic v2. Invalid payload shapes fail fast with 422 Unprocessable Entity.

### 1.5 Immutable Audit Logging
- Every administrative change, login attempt (successful or failed), privilege modification, and response operation records an immutable entry in the `audit_logs` table.
