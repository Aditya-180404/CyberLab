# CyberLab Purple-Team Validation & Attack Simulation Studio (Phase 9-10)

## 1. Overview & Purpose

The **CyberLab Purple-Team Validation Studio** provides continuous security control validation, atomic attack simulation, and detection efficacy benchmarking.

Rather than running unchecked or destructive offensive tools, CyberLab implements an **Atomic Validation Framework** (inspired by Atomic Red Team and MITRE ATT&CK):
- **Safe & Bounded**: Tests consist of controlled, benign probes, telemetry injections, and canary access queries designed strictly to test whether detection rules trigger.
- **Closed-Loop Correlation**: When a test is dispatched, the engine correlates resulting system telemetry directly against active SIEM rules and EDR agent alert pipelines.
- **Defensive Efficacy Measurement**: Quantifies whether existing detection engineering actually detects adversarial techniques across the MITRE ATT&CK matrix.

---

## 2. Core Architecture & Workflow

```
[Security Operator / Campaign Runner]
                 │
                 ▼
     [Atomic Scenario Dispatcher]
                 │
                 ├─────────────────────────────┬─────────────────────────────┐
                 ▼                             ▼                             ▼
       [Benign System Probes]        [Telemetry Injections]        [Canary File Checks]
      (e.g., uname -a, id)       (Failed SSH Brute Force)      (Access /etc/shadow)
                 │                             │                             │
                 └─────────────────────────────┼─────────────────────────────┘
                                               │
                                               ▼
                                    [SIEM Ingestion Engine]
                                               │
                                               ▼
                                   [Stateful Detection Rules]
                                               │
                                               ▼
                                    [Alert Generation Queue]
                                               │
                                               ▼
                                  [Validation Correlation]
                                 /                        \
                    [DETECTED (Rule Match)]     [MISSED (Detection Gap)]
```

---

## 3. Atomic Scenario Catalog

CyberLab ships with pre-configured atomic test scenarios categorized by MITRE ATT&CK tactics:

| Scenario ID | Technique | Name | Safe Payload Type | Expected SIEM Rule |
|---|---|---|---|---|
| `scen-t1082-sysinfo` | `T1082` | System Information Discovery | `BENIGN_COMMAND` | None (Baseline Activity) |
| `scen-t1033-userinfo` | `T1033` | Security Account Discovery | `BENIGN_COMMAND` | None (Baseline Activity) |
| `scen-t1110-brute-force` | `T1110` | SSH Authentication Brute Force | `TELEMETRY_INJECTION` | `RULE_AUTH_BRUTE_FORCE` |
| `scen-t1548-sudo-abuse` | `T1548.003` | Sudo Privilege Escalation Abuse | `TELEMETRY_INJECTION` | `RULE_PRIVILEGE_ESCALATION_SUDO` |
| `scen-t1003-shadow-dump` | `T1003.008` | /etc/shadow Canary File Access | `CANARY_FILE_CHECK` | `RULE_CREDENTIAL_DUMPING_SHADOW` |
| `scen-t1046-port-scan` | `T1046` | Network Service Port Recon | `PORT_PROBE` | `RULE_PORT_SCAN_RECON` |
| `scen-t1059-shell-exec` | `T1059.004` | Suspicious Shell Execution | `BENIGN_COMMAND` | `RULE_SUSPICIOUS_REVERSE_SHELL` |

---

## 4. Detection Efficacy & Metrics Formulation

### 4.1 Overall Detection Efficacy Rate

$$\text{Efficacy Rate (\%)} = \left(\frac{\text{Detected Validations}}{\text{Total Validations}}\right) \times 100$$

- **DETECTED**: The simulation produced telemetry that triggered the expected SIEM rule or generated an alert within the verification window.
- **MISSED**: The simulation executed, but no alerting rule fired, revealing an active detection blind spot.

### 4.2 Mean Time to Detect (MTTD)

$$\text{MTTD} = \frac{\sum_{i=1}^{N} (t_{\text{alert}, i} - t_{\text{dispatch}, i})}{N}$$

Measures the latency between adversarial action execution and SOC alert generation (typically under 0.1 seconds in CyberLab).

### 4.3 MITRE ATT&CK Coverage & Gap Categorization

- **COVERED (100%)**: Validated detection rule actively firing on simulation.
- **PARTIAL (1–79%)**: Intermittent detection or coverage on subset of telemetry.
- **GAP (0%)**: No active rule exists; immediate detection engineering action required.

---

## 5. REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/purple-team/scenarios` | Lists atomic attack simulation scenarios (filter by tactic) |
| `POST` | `/api/v1/purple-team/execute` | Dispatches single atomic test against target asset |
| `POST` | `/api/v1/purple-team/run-campaign` | Runs automated suite of atomic scenarios in batch |
| `GET` | `/api/v1/purple-team/executions` | Lists historical execution records and validation results |
| `GET` | `/api/v1/purple-team/coverage` | Returns MITRE ATT&CK defensive coverage matrix and gaps |
| `GET` | `/api/v1/purple-team/kpis` | Returns real-time Purple Team efficacy metrics and MTTD |

---

## 6. Verification & Test Suite

The engine is validated with 7 automated pytest tests in `backend/tests/test_purple_team.py`:
- `test_purple_team_scenario_seeding`: Verifies default scenario catalog seeding and listability.
- `test_execute_scenario_detected`: Validates that attack probes with matching rules transition to `DETECTED`.
- `test_execute_scenario_gap_missed`: Validates that baseline probes without rules record a `MISSED` gap.
- `test_run_purple_team_campaign`: Validates batch execution of purple team campaigns.
- `test_mitre_coverage_matrix`: Validates coverage calculation and gap identification.
- `test_purple_team_kpis`: Validates KPI calculations (Total Simulations, MTTD, by-tactic efficacy).
- `test_purple_team_api_endpoints`: Validates authenticated REST API calls.

Total backend test suite: **59 passing tests**.
Frontend production build: **Compiled successfully with zero TypeScript errors**.
