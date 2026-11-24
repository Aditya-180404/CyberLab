# CyberLab SOAR & Incident Response Engine (Phase 7)

## 1. Architectural Overview

The **Security Orchestration, Automation and Response (SOAR)** engine provides automated, semi-automated, and human-authorized containment workflows across distributed Linux agents, virtual machines, and simulated network infrastructures.

It closes the loop between **Detection (Phase 6 SIEM)** and **Remediation**, ensuring threats are neutralized rapidly while maintaining strict operational safety through **Human-in-the-Loop (HITL) approval gates**, **post-execution verification**, and **one-click state rollback**.

```
+---------------------------------------------------------------------------------------------+
|                                    CYBERLAB SOAR PIPELINE                                   |
+---------------------------------------------------------------------------------------------+
   | (SIEM Correlated Incident / Manual Analyst Trigger)
   v
+-----------------------------+
|  1. Playbook Selection      |  --> Evaluates trigger criteria and approval requirements
+-----------------------------+
   v
+-----------------------------+
|  2. Approval Gate (HITL)    |  --> High-impact actions queue in PENDING_APPROVAL state
+-----------------------------+
   | (Analyst Signoff / Rejection)
   v
+-----------------------------+
|  3. Action Execution        |  --> Dispatches ISOLATE_HOST, BLOCK_IP, SUSPEND_VM, REVOKE
+-----------------------------+
   v
+-----------------------------+
|  4. State Verification      |  --> Confirms target state (e.g. Agent ISOLATED, VM Suspended)
+-----------------------------+
   v
+-----------------------------+
|  5. Reversible Rollback     |  --> Cleanly reverses containment (RESTORE_HOST, UNBLOCK, RESUME)
+-----------------------------+
```

---

## 2. Containment Playbooks

CyberLab ships with 4 default containment playbooks:

| Playbook ID | Name | Trigger Event | Approval Required | Action Type |
|---|---|---|---|---|
| `playbook-host-quarantine` | Autonomous Endpoint Quarantine | `RULE_SUSPICIOUS_REVERSE_SHELL` | **Yes** (Approval Gate) | `ISOLATE_HOST` |
| `playbook-block-attacker-ip` | Perimeter Malicious IP Block | `RULE_AUTH_BRUTE_FORCE` | **No** (Autonomous) | `BLOCK_IP` |
| `playbook-vm-emergency-suspend`| Emergency VM Suspension | `ON_DEMAND` | **Yes** (Approval Gate) | `SUSPEND_VM` |
| `playbook-revoke-credentials` | Compromised Credential Killswitch| `ON_DEMAND` | **Yes** (Approval Gate) | `REVOKE_CREDENTIALS` |

---

## 3. Human-in-the-Loop (HITL) Governance

To prevent accidental denial-of-service on critical infrastructure:
- High-impact operations enter the `PENDING_APPROVAL` queue.
- Only authorized roles (`SUPER_ADMIN`, `SOC_MANAGER`, `SOC_ANALYST`) can authorize or reject actions.
- Rejection requires an auditable reason code.
- Every approval, execution, and rollback is logged to the immutable `audit_logs` table.

---

## 4. Post-Execution Verification & Rollback

### Automated Verification
After executing any response action, the SOAR engine verifies the target entity's state:
- **`ISOLATE_HOST`**: Verifies that the agent's database status is `ISOLATED` and the `ISOLATE` directive is queued in `pending_commands_json`.
- **`BLOCK_IP`**: Verifies drop rule registration across managed virtual bridges.
- **`SUSPEND_VM`**: Verifies hypervisor process state transition via `vmrun`.

### Clean State Rollback
Every containment action that mutates infrastructure supports one-click rollback:
- **Rolling back `ISOLATE_HOST`**: Automatically dispatches a `RESTORE` directive, resets the host status to `ONLINE`, and updates the action state to `ROLLED_BACK`.
- **Rolling back `BLOCK_IP`**: Automatically lifts the firewall filter.
- **Rolling back `SUSPEND_VM`**: Automatically powers the virtual machine back on.

---

## 5. REST API Reference

All endpoints require JWT Bearer authentication:

| Method | Endpoint | Description | Required Role |
|---|---|---|---|
| `GET` | `/api/v1/soar/playbooks` | List available playbooks. | Authenticated Users |
| `POST` | `/api/v1/soar/playbooks/{id}/execute` | Trigger a playbook against a target entity. | Analyst, Manager, Admin |
| `GET` | `/api/v1/soar/actions` | List action history (filter by `status`, `action_type`). | Authenticated Users |
| `POST` | `/api/v1/soar/actions/{id}/approve` | Authorize and execute a pending action. | Analyst, Manager, Admin |
| `POST` | `/api/v1/soar/actions/{id}/reject` | Reject a pending action with an audit reason. | Analyst, Manager, Admin |
| `POST` | `/api/v1/soar/actions/{id}/rollback` | Safely reverse an executed containment action. | Analyst, Manager, Admin |
| `GET` | `/api/v1/soar/kpis` | Real-time SOAR metrics and pending approval count. | Authenticated Users |
