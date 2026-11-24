# CyberLab v1.0.0 — Security Audit & Threat Model Report

**Audit Type**: White-Box Security Assessment & Vulnerability Analysis  
**Standard**: OWASP Top 10 API Security Risks (2023), CIS Controls v8, NIST SP 800-53 Rev. 5  
**Auditor Roles**: Principal Security Auditor, DevSecOps Engineer  

---

## 1. Executive Summary

This security audit conducted an exhaustive source-code review, cryptographic evaluation, privileged execution analysis, and threat modeling of the CyberLab platform.

### Finding Severity Summary

| Severity | Count | Summary of Risk |
|---|:---:|---|
| **CRITICAL** | 2 | Unauthenticated agent registration; Volatile/unpinned `SECRET_KEY` in multi-worker environments |
| **HIGH** | 3 | Static hardcoded seed passwords; Unrestricted agent HTTP communication; Broken access control on Sites/Vuln/Purple APIs |
| **MEDIUM** | 4 | Missing server-side JWT revocation on logout; No API rate limiting; Faux firewall containment in SOAR; Version-blind CVE matching |
| **LOW** | 2 | Missing dependencies in `requirements.txt`; Substring-only detection rule matching |
| **INFORMATIONAL**| 2 | Compliance score evidence static assertions; Simulated anchor injection in Digital Twin |

---

## 2. Classified Security Findings

### [SEC-01] CRITICAL: Unauthenticated Autonomous Agent Registration Endpoint
- **Severity**: **CRITICAL**
- **Affected Component**: `backend/app/api/v1/agents.py:94-140` (`POST /api/v1/agents/register`)
- **Description**: The endpoint for registering new endpoint agents requires zero authentication, enrollment secret, or pre-shared authorization key.
- **Evidence**:
  ```python
  @router.post("/agents/register", response_model=AgentRegisterResponse, status_code=status.HTTP_201_CREATED)
  def register_agent(payload: AgentRegisterRequest, db: Session = Depends(get_db)):
      raw_token = f"cla_{secrets.token_urlsafe(32)}"
      token_hash = get_password_hash(raw_token)
      agent_id = f"cl-agent-{secrets.token_hex(4)}"
  ```
- **Reproduction Procedure**:
  ```bash
  curl -X POST http://127.0.0.1:8000/api/v1/agents/register \
       -H "Content-Type: application/json" \
       -d '{"hostname": "rogue-host", "ip_address": "192.168.1.99", "agent_version": "1.0.0"}'
  # Returns 201 Created with valid bearer token
  ```
- **Impact**: Any unauthenticated network client can register an arbitrary number of fake agents, polluting the asset inventory, spoofing telemetry, flooding the database, and exhausting resources.
- **Recommended Correction**: Require an admin-generated enrollment token (e.g. `AGENT_ENROLLMENT_KEY`) or an administrator JWT Bearer token in the request header to authorize agent registration.
- **Verification Procedure**: Attempt registration without the enrollment header and confirm HTTP 401/403 is returned.

---

### [SEC-02] CRITICAL: Volatile Cryptographic Secret Key Generation in Multi-Worker Environments
- **Severity**: **CRITICAL**
- **Affected Component**: `backend/app/core/config.py:20`
- **Description**: When `SECRET_KEY` is not provided in an environment variable or `.env` file, the configuration generates a random 32-byte secret on import:
  ```python
  SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_hex(32))
  ```
- **Impact**: If CyberLab is deployed using multiple Uvicorn workers (`uvicorn app.main:app --workers 4`), each spawned worker process independently generates a unique `SECRET_KEY`. A JWT signed by worker A will be rejected as invalid signature by worker B, causing random, non-deterministic 401 Unauthorized errors for authenticated users. Furthermore, restarting the server immediately invalidates all active user sessions.
- **Recommended Correction**: Refuse to start in production mode (`ENVIRONMENT=production`) if `SECRET_KEY` is not explicitly set in the environment or persistent `.env` file. Raise a `RuntimeError` during startup if the key is missing or is set to a known insecure default.
- **Verification Procedure**: Start a multi-worker instance without `SECRET_KEY`; verify startup terminates with an explicit error.

---

### [SEC-03] HIGH: Hardcoded Default Administrative Credentials in Seed Script
- **Severity**: **HIGH**
- **Affected Component**: `backend/app/database/seed.py:40-66`
- **Description**: Default RBAC accounts are seeded with static credentials:
  - `admin@cyberlab.local` / `CyberLab@Admin2026!` (SUPER_ADMIN)
  - `analyst@cyberlab.local` / `Analyst@CyberLab2026!` (SOC_ANALYST)
  - `engineer@cyberlab.local` / `Engineer@CyberLab2026!` (NETWORK_ENGINEER)
  - `auditor@cyberlab.local` / `Auditor@CyberLab2026!` (AUDITOR)
- **Impact**: Deploying the application without an automated forced password reset allows attackers who read the open-source repository or documentation to obtain immediate administrative control over the platform.
- **Recommended Correction**: Introduce a `must_change_password: bool = True` column in the `User` model for seeded accounts, forcing immediate credential rotation upon first login.
- **Verification Procedure**: Log in with seeded credentials; verify API restricts all endpoints until password update endpoint is executed.

---

### [SEC-04] HIGH: Broken Access Control on Enterprise Sites, Vulnerabilities, and Purple-Team APIs
- **Severity**: **HIGH**
- **Affected Component**: `backend/app/api/v1/sites.py`, `backend/app/api/v1/vulnerability.py`, `backend/app/api/v1/purple_team.py`
- **Description**: Unlike `soar.py`, `topologies.py`, and `vms.py` which enforce `require_role([SUPER_ADMIN, ORG_ADMIN, ...])`, the following state-altering endpoints only check `get_current_user`:
  - `POST /api/v1/sites` (create site)
  - `PUT /api/v1/sites/{id}` (modify site)
  - `DELETE /api/v1/sites/{id}` (delete site)
  - `POST /api/v1/vulnerabilities/scan` (dispatch fleet scan)
  - `POST /api/v1/vulnerabilities/remediate` (modify CVE finding status)
  - `POST /api/v1/purple-team/execute` (dispatch simulation scenario)
- **Impact**: Any authenticated user (including low-privilege roles like `AUDITOR` or read-only accounts) can delete enterprise sites, trigger resource-heavy fleet scans, mark critical vulnerabilities as `MITIGATED` or `ACCEPTED_RISK` without authorization, or launch purple-team simulations.
- **Recommended Correction**: Add `require_role([UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.SECURITY_ENGINEER])` to all state-mutating endpoints across these modules.
- **Verification Procedure**: Issue `DELETE /api/v1/sites/{id}` as a user with `role="AUDITOR"`; verify HTTP 403 Forbidden is returned.

---

### [SEC-05] HIGH: Unrestricted Plaintext HTTP Agent Communication without Certificate Pinning
- **Severity**: **HIGH**
- **Affected Component**: `agent/cyberlab_agent.py:29-84`
- **Description**: The agent client defaults to `http://127.0.0.1:8000` using standard library `urllib.request`. When connected over network interfaces without TLS termination, all telemetry, FIM hash paths, process listings, socket tables, and authorization tokens (`cla_...`) are transmitted in cleartext.
- **Impact**: Network adversaries on the same segment can eavesdrop on agent tokens, capture endpoint telemetry, and tamper with policy instructions.
- **Recommended Correction**: Enforce HTTPS in production agent configuration; implement TLS certificate validation and server certificate fingerprint pinning.
- **Verification Procedure**: Configure agent with an HTTP URL in production mode; verify agent rejects non-TLS connections.

---

### [SEC-06] MEDIUM: Lack of Server-Side Token Revocation / Blacklist on Logout
- **Severity**: **MEDIUM**
- **Affected Component**: `backend/app/api/v1/auth.py:96-110`, `backend/app/core/dependencies.py`
- **Description**: The `POST /api/v1/auth/logout` endpoint only logs an audit trail event. It does not blacklist or invalidate the JWT token. The token remains cryptographically valid until its expiration (default 24 hours).
- **Impact**: If an access token is intercepted or copied before logout, the attacker can continue making authenticated requests for up to 24 hours regardless of whether the user logged out.
- **Recommended Correction**: Implement a Redis or database-backed token blacklist table, storing `jti` (JWT ID) claims of logged-out tokens until expiration.
- **Verification Procedure**: Log in, capture token, invoke logout endpoint, and attempt to query `/api/v1/auth/me` with the logged-out token. Confirm HTTP 401 is returned.

---

### [SEC-07] MEDIUM: Absence of API Rate Limiting
- **Severity**: **MEDIUM**
- **Affected Component**: `backend/app/main.py`, `backend/app/api/v1/auth.py`
- **Description**: No rate-limiting middleware (e.g. `slowapi` or leaky-bucket token limiter) is registered on API endpoints.
- **Impact**: Adversaries can execute credential-stuffing and brute-force attacks against `/api/v1/auth/login`, or flood `/api/v1/agents/register` and `/api/v1/siem/events` with volumetric traffic causing denial of service.
- **Recommended Correction**: Install and configure `slowapi` or deploy an Nginx reverse-proxy rate-limiting zone restricting login attempts to 5 per minute per IP.
- **Verification Procedure**: Send 20 rapid login attempts; verify requests beyond the limit receive HTTP 429 Too Many Requests.

---

### [SEC-08] MEDIUM: Faux Firewall Enforcement in SOAR Containment Engine
- **Severity**: **MEDIUM**
- **Affected Component**: `backend/app/soar/engine.py:173-185`
- **Description**: For `ActionType.BLOCK_IP` and `ActionType.UNBLOCK_IP`, the SOAR engine logs a message and sets `verified = True` without executing any firewall command (`nft` or `iptables`).
- **Impact**: SOC operators approving IP block containment playbooks are given a false sense of security; the attacking IP continues communicating unhindered.
- **Recommended Correction**: Integrate `LinuxKernelDriver.apply_nftables` or system netfilter commands to actually insert drop rules into the managed perimeter bridge or host table.
- **Verification Procedure**: Approve a `BLOCK_IP` action and verify rule presence with `nft list table inet cl_soar_filter`.

---

### [SEC-09] MEDIUM: Port-Only Vulnerability Matching Generating False Positives
- **Severity**: **MEDIUM**
- **Affected Component**: `backend/app/vulnerability/engine.py:182-186`
- **Description**: Vulnerability scanning matches CVEs if `svc_port == cve.port_hint`, causing modern patched services on standard ports (e.g., OpenSSH 9.6 on port 22 or Nginx on port 80) to be flagged with ancient critical CVEs (such as Debian OpenSSH weak keys from 2008 or Apache Slowloris from 2007).
- **Impact**: Skews risk scores, causes alert fatigue, and creates misleading executive risk reporting.
- **Recommended Correction**: Match CVEs only when service name matches AND version banner matches the vulnerable version range, or when explicitly tagged as a known vulnerable target VM.
- **Verification Procedure**: Scan an asset running modern OpenSSH on port 22; verify `CVE-2008-0166` is NOT assigned unless the banner indicates a vulnerable release.

---

## 3. Cryptographic & Secret Management Assessment

| Asset / Parameter | Implementation | Assessment | Finding / Recommendation |
|---|---|---|---|
| Password Hashing | `bcrypt.hashpw` with 12 rounds | **SECURE** | Industry standard, strong salt. |
| JWT Signing Algorithm | `HS256` (HMAC with SHA-256) | **ACCEPTABLE** | Recommend transitioning to `RS256` / `EdDSA` for enterprise multi-service deployments. |
| JWT Expiration | 1,440 minutes (24 hours) | **MARGINAL** | 24 hours is excessive for administrative sessions. Recommend 15–60 minutes with refresh tokens. |
| Agent Token Generation | `secrets.token_urlsafe(32)` | **SECURE** | 256-bit cryptographically secure pseudorandom token. |
| Secret Key Persistence | `os.getenv("SECRET_KEY", random)` | **INSECURE** | Volatile in multi-worker production without `.env`. Requires mandatory configuration check. |
