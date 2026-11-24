# CyberLab Distributed Linux Agent Platform Architecture

## 1. Architectural Purpose & Overview

The **Distributed Linux Agent** is an autonomous, lightweight endpoint security client engineered to run on managed Linux workstations, servers, and target lab machines (such as Parrot OS, Ubuntu, Debian, and Kali Linux).

It provides real-time endpoint visibility and response without exposing an unrestricted remote shell:
1. **Outbound Connection Model**: All communication is outbound from the agent to the central CyberLab server (`POST /api/v1/agents/*`). The agent never listens on an open inbound TCP port, preventing attackers from weaponizing the agent.
2. **Cryptographic Identity & Registration**: Each agent receives a unique UUID (`cl-agent-<uuid>`) and a cryptographically generated 256-bit authentication token during registration.
3. **Heartbeat & Telemetry Ingestion**: Periodic heartbeat transmission (default 10s) with CPU, RAM, and disk telemetry.
4. **Endpoint Telemetry Telemetry**:
   - **System Inventory**: Hostname, OS, kernel, uptime, hardware specs.
   - **Process Monitoring**: Running processes, PIDs, PPIDs, executable paths, and command lines.
   - **Network Socket Monitoring**: Listening TCP/UDP ports and active remote IP connections.
   - **Authentication Auditing**: SSH logins, failed password attempts, and `sudo` activity.
   - **File Integrity Monitoring (FIM)**: SHA-256 cryptographic baselines for critical system files (`/etc/passwd`, `/etc/shadow`, `/etc/sudoers`, `/etc/ssh/sshd_config`).
5. **Controlled Endpoint Isolation**: Executes authorized host network isolation by restricting outbound and inbound traffic while preserving the secure management channel to the CyberLab server.
6. **Offline Policy Persistence**: Enforces local FIM and security rules even when central server connectivity is temporarily lost.

---

## 2. Agent Communication & Authentication Flow

```
+---------------------------+                      +---------------------------+
|   Distributed Agent Node  |                      |  Central CyberLab Server  |
|   (Parrot OS / VM / Host) |                      |    (FastAPI / Database)   |
+-------------+-------------+                      +-------------+-------------+
              │                                                  │
              │  1. POST /api/v1/agents/register                 │
              │  (Hostname, OS, Kernel, Hardware Specs)          │
              ├─────────────────────────────────────────────────►│
              │                                                  │ Verify Organization
              │  2. Return Agent ID & Secret Token               │ Store Hash in Database
              │◄─────────────────────────────────────────────────┤
              │                                                  │
              │  3. Local Config Persistence                     │
              │  (/etc/cyberlab/agent.json)                      │
              │                                                  │
              │  4. POST /api/v1/agents/heartbeat (every 10s)    │
              │  (Header: Authorization: Bearer <agent_token>)   │
              ├─────────────────────────────────────────────────►│ Update Last Heartbeat
              │  Returns: Pending Policy / Action Directives     │ Check Commands Queue
              │◄─────────────────────────────────────────────────┤
              │                                                  │
              │  5. POST /api/v1/agents/telemetry                │
              │  (Processes, Sockets, Auth Events, FIM Deltas)   │
              ├─────────────────────────────────────────────────►│ Stream to SIEM Engine
              │                                                  │ (Phase 6 Correlation)
```

---

## 3. File Integrity Monitoring (FIM) Specification

- **Monitored Targets (Default)**:
  - `/etc/passwd`
  - `/etc/shadow`
  - `/etc/sudoers`
  - `/etc/ssh/sshd_config`
  - `/etc/hosts`
- **Baseline Generation**: On initial startup, the agent computes `SHA-256` checksums, file sizes, and modification timestamps for each monitored file.
- **Delta Detection**: Each polling cycle re-hashes monitored targets. If a checksum change, creation, or deletion is detected, an alert payload is formatted and transmitted to the central server:
  ```json
  {
    "event_type": "FIM_MODIFICATION",
    "file_path": "/etc/passwd",
    "old_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "new_hash": "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e",
    "timestamp": "2026-11-24T15:20:00Z"
  }
  ```

---

## 4. Controlled Endpoint Isolation Protocol

When an analyst triggers an **Isolate Endpoint** command from the SOC dashboard:
1. The server queues an `ISOLATE` action in the agent's pending command stream.
2. During the next heartbeat, the agent receives the isolation order.
3. The agent validates the action and applies a restricted `iptables` or `nftables` policy:
   - **Allowed**: Communication only with the CyberLab server IP and management port (`8000`).
   - **Blocked**: All other inbound and outbound traffic to prevent lateral movement or data exfiltration.
4. The agent reports `ISOLATED` status back to the server.
5. Restoration (`RESTORE` command) flushes the isolation rules and returns to normal operation.
