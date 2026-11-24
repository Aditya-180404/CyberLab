# CyberLab v1.0.0 — Distributed Linux Agent Security Audit

**Component Audited**: `agent/cyberlab_agent.py`, `backend/app/api/v1/agents.py`, `backend/app/models/agent.py`  
**Auditor Roles**: Principal Security Auditor, DevSecOps Engineer, Endpoint Security Specialist  

---

## 1. Agent Architecture & Lifecycle Analysis

The CyberLab Agent is a lightweight, standalone Python daemon designed to run on managed Linux endpoints (Kali, Parrot, Ubuntu, Debian, CentOS).

```
   ┌───────────────────────┐                    ┌───────────────────────┐
   │    CyberLab Server    │                    │    Endpoint Host      │
   │  (FastAPI /api/v1/)   │                    │  (cyberlab_agent.py)  │
   └──────────┬────────────┘                    └───────────┬───────────┘
              │                                             │
              │ 1. POST /agents/register (Payload)          │
              │◄────────────────────────────────────────────┤
              │    (Issues: cl-agent-XXXX + cla_TOKEN)      │
              ├────────────────────────────────────────────►│ 2. Caches identity in
              │                                             │    cyberlab_agent_config.json
              │ 3. POST /agents/heartbeat (Every 10s)       │
              │◄────────────────────────────────────────────┤
              │    (Returns: pending_commands: [])          │
              ├────────────────────────────────────────────►│
              │                                             │
              │ 4. POST /agents/telemetry (Every 20s)       │
              │◄────────────────────────────────────────────┤
              │    (Processes, Sockets, FIM Alerts)         │
              │                                             │
              │ 5. SOAR Command: "ISOLATE"                  │
              ├────────────────────────────────────────────►│ 6. apply_isolation()
```

---

## 2. In-Depth Security & Integrity Findings

### Finding 1: Unauthenticated Registration Endpoint (Critical Risk)
- **Code Path**: `backend/app/api/v1/agents.py:94-140`
- **Issue**: Any network entity capable of reaching `/api/v1/agents/register` can register arbitrary endpoints into the platform.
- **Vulnerability Mechanism**: The registration endpoint requires no pre-shared enrollment key, installation token, or administrator credentials.
- **Risk**: An attacker on the local network or internet can flood the database with millions of fake agents or register rogue endpoints that spoof hostnames and IP addresses.

### Finding 2: Plaintext HTTP Transport by Default
- **Code Path**: `agent/cyberlab_agent.py:29-84`
- **Issue**: The agent defaults to `http://127.0.0.1:8000` via Python's standard `urllib.request`.
- **Vulnerability Mechanism**: There is no enforcement of TLS (`https://`), no certificate pinning, and no mutual TLS (mTLS) authentication.
- **Risk**: Over local Wi-Fi or unsegmented lab networks, all agent credentials (`cla_...`), running process command lines, listening sockets, and FIM hashes are transmitted in plaintext, vulnerable to passive interception and active man-in-the-middle (MITM) tampering.

### Finding 3: Faux Isolation & Containment Enforcement
- **Code Path**: `agent/cyberlab_agent.py:208-219`
- **Issue**:
  ```python
  def apply_isolation(self) -> None:
      """Applies local network isolation restricting non-CyberLab traffic."""
      print("[!] ISOLATION ORDER RECEIVED. Locking down network traffic...")
      self.is_isolated = True
      self.save_local_config()
  ```
- **Operational Reality**: When a SOAR playbook triggers an endpoint quarantine, the agent sets `self.is_isolated = True` and writes it to disk. **It does NOT execute any firewall commands (`nft` or `iptables`)**. The endpoint remains completely capable of sending and receiving lateral network traffic.
- **Correction Required**: Implement genuine netfilter quarantine rules (e.g., dropping all egress/ingress except outbound HTTPS to the CyberLab server IP).

### Finding 4: Unimplemented Authentication Log Parsing
- **Code Path**: `agent/cyberlab_agent.py:268`
- **Issue**: In `send_telemetry`, the agent hardcodes:
  ```python
  "auth_events": []
  ```
- **Operational Reality**: The agent claims in its policy to monitor authentication logs (`monitor_auth_logs: True`), but does not tail `/var/log/auth.log` or `/var/log/secure`. Authentication telemetry events must currently be fed into the SIEM via API or purple-team injection.

### Finding 5: Organization Mismatch during Registration
- **Code Path**: `backend/app/api/v1/agents.py:103`
- **Issue**: The registration handler hardcodes `org_id = "default-org"`, whereas `seed_database()` creates an organization with a generated UUID. If multi-tenancy or organization-specific filtering is enabled, newly registered agents are invisible to the primary organization until manually updated in the database.

---

## 3. Cryptographic Token & Revocation Lifecycle

- **Token Generation**: Uses `secrets.token_urlsafe(32)` generating a 256-bit entropy bearer token prefixed with `cla_`.
- **Token Storage**: The central database stores only the bcrypt hash of the token (`agent.agent_token_hash = get_password_hash(raw_token)`).
- **Authentication**: Verified via `verify_password(token, agent.agent_token_hash)` on each heartbeat and telemetry submission.
- **Credential Revocation**: Supported via `POST /api/v1/agents/{id}/revoke`. When invoked:
  - `agent.status = AgentStatus.REVOKED`
  - `agent.agent_token_hash = "REVOKED_KILLSWITCH"`
  - Subsequent requests from the agent return HTTP 403 Forbidden. The agent script intercepts 403 and self-terminates (`sys.exit(1)`).
- **Offline Survivability**: The agent persists its `agent_id`, `agent_token`, FIM baselines, and policy in `cyberlab_agent_config.json`. If the central server becomes unreachable, the agent continues calculating FIM deltas locally, buffering alerts until reconnection.
