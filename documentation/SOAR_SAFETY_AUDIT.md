# CyberLab v1.0.0 — SOAR & Incident Response Safety Audit

**Component Audited**: `backend/app/soar/` (`engine.py`), `backend/app/api/v1/soar.py`, `backend/app/models/soar.py`  
**Auditor Roles**: SOC Architect, Principal Security Auditor, DevSecOps Engineer  

---

## 1. SOAR Workflow & Approval Gate Architecture

CyberLab's Security Orchestration, Automation, and Response (SOAR) module coordinates response playbooks, human-in-the-loop (HITL) approval gates, and verified state rollback.

```
                      TRIGGER EVENT (SIEM Alert / On-Demand)
                                        │
                                        ▼
                           ┌─────────────────────────┐
                           │    SOAREngine.create    │
                           └────────────┬────────────┘
                                        │
                      ┌─────────────────┴─────────────────┐
                      │ Requires Human Approval?          │
                      ▼                                   ▼
             [requires_approval = True]           [requires_approval = False]
                      │                                   │
                      ▼                                   ▼
             ┌─────────────────┐                 ┌─────────────────┐
             │ Status: PENDING │                 │ Status: APPROVED│
             └────────┬────────┘                 └────────┬────────┘
                      │                                   │
      ┌───────────────┴───────────────┐                   │
      ▼                               ▼                   │
[User Approves]                 [User Rejects]            │
Status: APPROVED                Status: REJECTED          │
      │                                                   │
      └───────────────────────┬───────────────────────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │ Status: EXECUTING│
                     └────────┬─────────┘
                              │
                    Action Execution Logic
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
       [Success]                          [Failure]
Status: COMPLETED                  Status: FAILED
verified = True                    verified = False
      │
      ▼
Rollback Capability
(Reversible: ISOLATE_HOST, BLOCK_IP, SUSPEND_VM)
```

---

## 2. Playbook Catalog & Action Type Verification

| Playbook ID | Trigger Event | Approval Required | Target Type | Action Type | Real System Execution Verified? |
|---|---|:---:|---|---|:---:|
| `playbook-host-quarantine` | `RULE_SUSPICIOUS_REVERSE_SHELL` | **YES** | Host / Agent | `ISOLATE_HOST` | **PARTIAL** (State set in DB; Agent only sets in-memory flag) |
| `playbook-block-attacker-ip`| `RULE_AUTH_BRUTE_FORCE` | **NO** (Auto) | IP Address | `BLOCK_IP` | **FAUX / STUBBED** (No firewall command executed) |
| `playbook-vm-emergency-suspend` | `ON_DEMAND` | **YES** | Virtual Machine | `SUSPEND_VM` | **VERIFIED** (Invokes `/usr/bin/vmrun -T ws suspend`) |
| `playbook-revoke-credentials` | `ON_DEMAND` | **YES** | Agent | `REVOKE_CREDENTIALS` | **VERIFIED** (Scrambles token hash to killswitch) |

---

## 3. Critical Safety Discrepancies

### 1. Faux Containment in Perimeter IP Blocking (`BLOCK_IP`)
- **Code Reference**: `backend/app/soar/engine.py:173-177`
  ```python
  elif action.action_type == ActionType.BLOCK_IP:
      ip_to_block = action.target_id
      verified = True
      verification_details = f"Firewall drop rule applied for IP '{ip_to_block}' across managed virtual bridges."
      log_lines.append(f"[+] IP {ip_to_block} blocked at perimeter.")
  ```
- **Auditor Assessment**:
  - The engine marks `action.verified = True` and writes that a "Firewall drop rule applied" in the execution log.
  - **In reality, no system command or netfilter rule is executed**.
  - **Risk**: SOC analysts approving this playbook are given false confirmation that an active threat IP has been neutralized.

### 2. Logical vs. Physical Host Isolation (`ISOLATE_HOST`)
- **Code Reference**: `backend/app/soar/engine.py:124-149` & `agent/cyberlab_agent.py:208-213`
  - Backend sets `agent.status = AgentStatus.ISOLATED` and queues `"ISOLATE"` in `agent.pending_commands_json`.
  - When the agent polls its heartbeat, it receives `"ISOLATE"` and executes `apply_isolation()`.
  - In `cyberlab_agent.py`, `apply_isolation()` merely sets `self.is_isolated = True` and saves to JSON.
  - **Auditor Assessment**: Lateral network traffic is NOT blocked at the kernel network stack. To be genuinely effective, the agent or server must inject an `nftables` drop policy.

### 3. Genuine Hypervisor Forensic Suspension (`SUSPEND_VM`)
- **Code Reference**: `backend/app/soar/engine.py:187-198`
  - Resolves VM record in database.
  - Calls `vm_manager.power_vm(db, vm.id, "suspend")`.
  - Invokes `vmrun -T ws suspend <config_path> soft`.
  - **Auditor Assessment**: Genuinely freezes VM guest memory and CPU state for incident forensics. Rollback correctly unfreezes the VM by issuing a `start` command.

---

## 4. Rollback Verification

Rollback is supported for state-modifying actions via `POST /api/v1/soar/actions/{id}/rollback`:
- **Host Quarantine Rollback**: Queues `"RESTORE"` command to agent and restores database status to `AgentStatus.ONLINE`.
- **IP Unblock Rollback**: Updates database state and records audit log.
- **VM Suspension Rollback**: Invokes `vmrun start` to resume the suspended virtual machine.
- **Credential Revocation Rollback**: Strictly rejected (`rollback_supported = False`); once credentials are scrambled via killswitch, an agent cannot be restored without re-registration.
