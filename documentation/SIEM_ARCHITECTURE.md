# CyberLab SIEM, Detection Engine & MITRE ATT&CK Mapping (Phase 6)

## 1. Architectural Overview

The **CyberLab SIEM & Detection Engine** centralizes, normalizes, and correlates security telemetry collected across distributed Linux agents (Phase 4), real VMware virtual machines (Phase 3), and simulated network environments (Phase 2).

It transforms raw log streams into structured, stateful detections mapped to the **MITRE ATT&CK Enterprise Framework**, automatically aggregating alerts into correlated **Security Incidents** to provide Root Cause Analysis (RCA).

```
+---------------------------------------------------------------------------------------------+
|                                    CYBERLAB SIEM PIPELINE                                   |
+---------------------------------------------------------------------------------------------+
   | (Agents / Syslog / Auth Logs / Sockets / FIM)
   v
+-----------------------------+
|  1. Event Ingestion Layer   |  --> Normalized ECS-compliant SecurityEvent Schema
+-----------------------------+
   v
+-----------------------------+
|  2. Stateful Rule Engine    |  --> Evaluates T1110, T1548.003, T1003.008, T1059.004, T1046
+-----------------------------+
   v
+-----------------------------+
|  3. Alert Aggregation       |  --> Deduplicates repetitive alerts within sliding time windows
+-----------------------------+
   v
+-----------------------------+
|  4. Incident Correlation    |  --> Automatically correlates multi-stage attacks on same asset
+-----------------------------+
   v
+-----------------------------+
|  5. MITRE ATT&CK Heatmap    |  --> Real-time tactical matrix mapping across 9 enterprise tactics
+-----------------------------+
```

---

## 2. Normalized Security Event Data Model

All events conform to the `SecurityEvent` schema (`security_events` table):

| Field | Type | Description |
|---|---|---|
| `id` | `String(36)` | Unique event identifier (`evt-XXXXXXXX`). |
| `timestamp` | `DateTime` | UTC event timestamp (indexed for time-range queries). |
| `category` | `String(50)` | `AUTHENTICATION`, `PROCESS_EXECUTION`, `NETWORK_CONNECTION`, `FILE_INTEGRITY`, `SYSTEM_LOG`. |
| `severity` | `String(20)` | `INFORMATIONAL`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`. |
| `action` | `String(30)` | `SUCCESS`, `FAILURE`, `DETECTED`, `BLOCKED`. |
| `message` | `Text` | Normalized human-readable event description. |
| `hostname` | `String(100)` | Target host / virtual machine identifier. |
| `source_ip` | `String(45)` | Remote or local source IP address. |
| `destination_ip` | `String(45)` | Destination target IP address. |
| `mitre_tactic` | `String(50)` | MITRE tactic (e.g. `Credential Access`, `Privilege Escalation`). |
| `mitre_technique_id`| `String(20)` | MITRE technique ID (e.g. `T1110`, `T1548.003`). |
| `mitre_technique_name`| `String(100)`| MITRE technique name (e.g. `Brute Force`). |

---

## 3. Stateful Detection Rules

The engine runs non-blocking, stateful evaluation on every ingested event:

### 1. `RULE_AUTH_BRUTE_FORCE` (MITRE T1110: Brute Force)
- **Tactic**: `Credential Access`
- **Severity**: `HIGH`
- **Logic**: Detects $\ge 3$ consecutive failed authentication attempts against the same host or from the same source IP within a 5-minute sliding window.

### 2. `RULE_PRIVILEGE_ESCALATION_SUDO` (MITRE T1548.003: Sudo and Sudo Caching)
- **Tactic**: `Privilege Escalation`
- **Severity**: `HIGH`
- **Logic**: Inspects authentication logs for unauthorized `sudo` elevation attempts, invalid sudoers entries, or failed `su root` commands.

### 3. `RULE_CREDENTIAL_DUMPING_SHADOW` (MITRE T1003.008: /etc/passwd and /etc/shadow)
- **Tactic**: `Credential Access`
- **Severity**: `CRITICAL`
- **Logic**: Detects unexpected modifications or access violations to `/etc/shadow`, `/etc/passwd`, or `/etc/sudoers` reported by the agent's File Integrity Monitoring (FIM) engine.

### 4. `RULE_SUSPICIOUS_REVERSE_SHELL` (MITRE T1059.004: Unix Shell)
- **Tactic**: `Execution`
- **Severity**: `CRITICAL`
- **Logic**: Analyzes process execution telemetry for interactive shell redirect patterns (`/bin/bash -i`, `nc -e`, `pty.spawn`, `sh -i >& /dev/tcp`).

### 5. `RULE_PORT_SCAN_RECON` (MITRE T1046: Network Service Discovery)
- **Tactic**: `Discovery`
- **Severity**: `MEDIUM`
- **Logic**: Identifies rapid connection probes across multiple distinct port endpoints indicative of reconnaissance scanners.

---

## 4. Multi-Stage Incident Correlation Engine

Individual alerts are automatically correlated into unified **`SecurityIncident`** objects:
1. **Host-Centric Correlation**: If an endpoint suffers **2 or more distinct threat vectors** (e.g., *Authentication Brute Force* followed by *Sudo Privilege Escalation*, or *Credential Dumping* followed by *Reverse Shell*), the engine automatically promotes the alerts into a single High or Critical `SecurityIncident`.
2. **Tactical Multi-Stage Mapping**: Summarizes the attacker's trajectory across the MITRE ATT&CK chain (e.g. `Credential Access -> Privilege Escalation`).
3. **Alert Deduplication**: Repetitive firing of the same rule on a host within 15 minutes increments the `evidence_count` rather than flooding the analyst's queue with duplicate alerts.

---

## 5. Synthetic Attack Simulation Engine

To enable purple-teaming validation without risking production infrastructure, the SIEM includes an internal attack simulation generator:
- **`brute_force`**: Generates a multi-attempt SSH failed login sequence against a target host (e.g. `Metasploitable 2`).
- **`privilege_escalation`**: Injects unauthorized sudo execution attempt telemetry.
- **`credential_dumping`**: Generates a critical FIM hash change event on `/etc/shadow`.
- **`reverse_shell`**: Injects interactive `/bin/bash` TCP redirection telemetry.

---

## 6. REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/siem/events` | Stream normalized events (filter by `category`, `severity`, `hostname`, `search`). |
| `POST` | `/api/v1/siem/events` | Ingest new event and trigger real-time detection rules. |
| `GET` | `/api/v1/siem/alerts` | List aggregated security alerts with MITRE technique tags. |
| `GET` | `/api/v1/siem/incidents` | List correlated multi-stage security incidents. |
| `GET` | `/api/v1/siem/mitre` | Retrieve MITRE ATT&CK matrix heatmap with active hit counts. |
| `GET` | `/api/v1/siem/kpis` | Real-time SIEM KPI counters (event volume, open alerts, active incidents). |
| `POST` | `/api/v1/siem/simulate` | Execute offensive simulation scenario against a designated target host. |
