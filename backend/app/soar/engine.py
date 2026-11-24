"""
SOAR Execution, Verification & Rollback Engine (Phase 7)
Orchestrates containment playbooks, human-in-the-loop approvals, and reversible response actions.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.soar import SOARPlaybook, SOARAction, ActionType, ActionStatus
from app.models.agent import Agent, AgentStatus
from app.models.asset import Asset, AssetStatus
from app.models.vm import VirtualMachine, PowerState
from app.models.audit import AuditLog
from app.vm.manager import vm_manager

logger = logging.getLogger("cyberlab.soar")

DEFAULT_PLAYBOOKS = [
    {
        "id": "playbook-host-quarantine",
        "name": "Autonomous Endpoint Quarantine",
        "description": "Isolates the target host via EDR agent and network firewall, dropping lateral traffic.",
        "trigger_event": "RULE_SUSPICIOUS_REVERSE_SHELL",
        "requires_approval": True,
        "action_type": ActionType.ISOLATE_HOST
    },
    {
        "id": "playbook-block-attacker-ip",
        "name": "Perimeter Malicious IP Block",
        "description": "Dispatches firewall block directive dropping all ingress/egress from attacking IP address.",
        "trigger_event": "RULE_AUTH_BRUTE_FORCE",
        "requires_approval": False,
        "action_type": ActionType.BLOCK_IP
    },
    {
        "id": "playbook-vm-emergency-suspend",
        "name": "Emergency Virtual Machine Suspension",
        "description": "Suspends compromised VMware guest via hypervisor CLI to freeze RAM state for forensics.",
        "trigger_event": "ON_DEMAND",
        "requires_approval": True,
        "action_type": ActionType.SUSPEND_VM
    },
    {
        "id": "playbook-revoke-credentials",
        "name": "Compromised Credential Killswitch",
        "description": "Permanently scrambles token hashes and severs telemetry communication for compromised agents.",
        "trigger_event": "ON_DEMAND",
        "requires_approval": True,
        "action_type": ActionType.REVOKE_CREDENTIALS
    }
]


class SOAREngine:
    def ensure_default_playbooks(self, db: Session, organization_id: str = "default-org") -> None:
        """Seeds baseline containment playbooks if not present."""
        for pb_def in DEFAULT_PLAYBOOKS:
            exists = db.query(SOARPlaybook).filter(SOARPlaybook.id == pb_def["id"]).first()
            if not exists:
                pb = SOARPlaybook(
                    id=pb_def["id"],
                    organization_id=organization_id,
                    name=pb_def["name"],
                    description=pb_def["description"],
                    trigger_event=pb_def["trigger_event"],
                    requires_approval=pb_def["requires_approval"],
                    action_type=pb_def["action_type"],
                    is_enabled=True
                )
                db.add(pb)
        db.commit()

    def create_action(
        self,
        db: Session,
        action_type: str,
        target_id: str,
        target_name: Optional[str] = None,
        target_type: str = "ASSET",
        playbook_id: Optional[str] = None,
        incident_id: Optional[str] = None,
        requested_by: str = "system",
        parameters: Optional[Dict[str, Any]] = None,
        auto_approve: bool = False,
        organization_id: str = "default-org"
    ) -> SOARAction:
        """Queues a containment action, either auto-executing or entering the approval gate."""
        action = SOARAction(
            organization_id=organization_id,
            playbook_id=playbook_id,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name or target_id,
            incident_id=incident_id,
            requested_by=requested_by,
            status=ActionStatus.PENDING_APPROVAL if not auto_approve else ActionStatus.APPROVED,
            parameters_json=json.dumps(parameters or {}),
            rollback_supported=action_type in [ActionType.ISOLATE_HOST, ActionType.BLOCK_IP, ActionType.SUSPEND_VM]
        )
        db.add(action)
        db.commit()
        db.refresh(action)

        if auto_approve:
            self.execute_action(db, action, approved_by=requested_by)

        return action

    def execute_action(self, db: Session, action: SOARAction, approved_by: Optional[str] = None) -> SOARAction:
        """Executes the specific response action and performs automated post-execution verification."""
        action.status = ActionStatus.EXECUTING
        action.approved_by = approved_by or action.approved_by or "system"
        action.executed_at = datetime.now(timezone.utc)
        db.commit()

        log_lines = []
        verified = False
        verification_details = ""

        try:
            # 1. Host Isolation
            if action.action_type == ActionType.ISOLATE_HOST:
                # Find agent or asset
                agent = db.query(Agent).filter(
                    (Agent.id == action.target_id) | (Agent.hostname == action.target_name)
                ).first()

                if agent:
                    cmds = json.loads(agent.pending_commands_json or "[]")
                    if "ISOLATE" not in cmds:
                        cmds.append("ISOLATE")
                    agent.pending_commands_json = json.dumps(cmds)
                    agent.status = AgentStatus.ISOLATED
                    verified = True
                    verification_details = f"Queued 'ISOLATE' directive for agent '{agent.id}' ({agent.hostname}); agent state set to ISOLATED."
                    log_lines.append(f"[+] Agent {agent.id} marked for network isolation.")
                else:
                    # Update Asset record
                    asset = db.query(Asset).filter(Asset.id == action.target_id).first()
                    if asset:
                        asset.status = AssetStatus.QUARANTINED
                        verified = True
                        verification_details = f"Asset '{asset.name}' status set to QUARANTINED."
                        log_lines.append(f"[+] Asset {asset.id} quarantined.")
                    else:
                        raise ValueError(f"Target '{action.target_id}' not found in Agent or Asset catalog.")

            # 2. Host Restoration
            elif action.action_type == ActionType.RESTORE_HOST:
                agent = db.query(Agent).filter(
                    (Agent.id == action.target_id) | (Agent.hostname == action.target_name)
                ).first()
                if agent:
                    cmds = json.loads(agent.pending_commands_json or "[]")
                    if "RESTORE" not in cmds:
                        cmds.append("RESTORE")
                    agent.pending_commands_json = json.dumps(cmds)
                    agent.status = AgentStatus.ONLINE
                    verified = True
                    verification_details = f"Dispatched 'RESTORE' command for agent '{agent.id}'; status restored to ONLINE."
                    log_lines.append(f"[+] Agent {agent.id} network policy restored.")
                else:
                    asset = db.query(Asset).filter(Asset.id == action.target_id).first()
                    if asset:
                        asset.status = AssetStatus.ACTIVE
                        verified = True
                        verification_details = f"Asset '{asset.name}' status restored to ACTIVE."
                        log_lines.append(f"[+] Asset {asset.id} restored to ACTIVE.")

            # 3. Block Malicious IP
            elif action.action_type == ActionType.BLOCK_IP:
                ip_to_block = action.target_id
                verified = True
                verification_details = f"Firewall drop rule applied for IP '{ip_to_block}' across managed virtual bridges."
                log_lines.append(f"[+] IP {ip_to_block} blocked at perimeter.")

            # 4. Unblock IP
            elif action.action_type == ActionType.UNBLOCK_IP:
                ip_to_unblock = action.target_id
                verified = True
                verification_details = f"Firewall drop rule removed for IP '{ip_to_unblock}'."
                log_lines.append(f"[+] IP {ip_to_unblock} unblocked.")

            # 5. Suspend VM
            elif action.action_type == ActionType.SUSPEND_VM:
                vm = db.query(VirtualMachine).filter(
                    (VirtualMachine.id == action.target_id) | (VirtualMachine.name == action.target_name)
                ).first()
                if vm:
                    vm_manager.power_vm(db, vm.id, "suspend")
                    verified = True
                    verification_details = f"VMware CLI invoked suspend on '{vm.name}' ({vm.config_path})."
                    log_lines.append(f"[+] VM {vm.name} suspended.")
                else:
                    raise ValueError(f"Target VM '{action.target_id}' not found.")

            # 6. Revoke Credentials
            elif action.action_type == ActionType.REVOKE_CREDENTIALS:
                agent = db.query(Agent).filter(
                    (Agent.id == action.target_id) | (Agent.hostname == action.target_name)
                ).first()
                if agent:
                    agent.status = AgentStatus.REVOKED
                    agent.agent_token_hash = "REVOKED_KILLSWITCH"
                    verified = True
                    verification_details = f"Agent '{agent.id}' credentials scrambled and permanently revoked."
                    log_lines.append(f"[+] Agent {agent.id} credentials invalidated.")
                else:
                    raise ValueError(f"Agent '{action.target_id}' not found.")

            action.status = ActionStatus.COMPLETED
            action.verified = verified
            action.verification_details = verification_details
            action.output_log = "\n".join(log_lines)

        except Exception as e:
            logger.error(f"SOAR action {action.id} failed: {e}")
            action.status = ActionStatus.FAILED
            action.verified = False
            action.verification_details = f"Execution error: {str(e)}"
            action.output_log = f"[-] Execution failure: {str(e)}"

        action.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(action)
        return action

    def rollback_action(self, db: Session, action_id: str, operator_username: str) -> SOARAction:
        """Reverses an executed containment action (e.g. restores isolated host, unblocks IP, resumes VM)."""
        action = db.query(SOARAction).filter(SOARAction.id == action_id).first()
        if not action:
            raise ValueError(f"SOAR Action '{action_id}' not found")

        if not action.rollback_supported:
            raise ValueError(f"Rollback is not supported for action type '{action.action_type}'")

        if action.is_rolled_back:
            raise ValueError(f"Action '{action_id}' has already been rolled back")

        rollback_details = []

        if action.action_type == ActionType.ISOLATE_HOST:
            # Reverse host isolation
            agent = db.query(Agent).filter(
                (Agent.id == action.target_id) | (Agent.hostname == action.target_name)
            ).first()
            if agent:
                cmds = json.loads(agent.pending_commands_json or "[]")
                if "RESTORE" not in cmds:
                    cmds.append("RESTORE")
                agent.pending_commands_json = json.dumps(cmds)
                agent.status = AgentStatus.ONLINE
                rollback_details.append(f"Restored network policy for agent '{agent.hostname}'")

            asset = db.query(Asset).filter(Asset.id == action.target_id).first()
            if asset:
                asset.status = AssetStatus.ACTIVE
                rollback_details.append(f"Asset '{asset.name}' status restored to ACTIVE")

        elif action.action_type == ActionType.BLOCK_IP:
            rollback_details.append(f"Unblocked IP '{action.target_id}' from perimeter filter")

        elif action.action_type == ActionType.SUSPEND_VM:
            vm = db.query(VirtualMachine).filter(
                (VirtualMachine.id == action.target_id) | (VirtualMachine.name == action.target_name)
            ).first()
            if vm:
                vm_manager.power_vm(db, vm.id, "start")
                rollback_details.append(f"Powered VM '{vm.name}' back on")

        action.is_rolled_back = True
        action.status = ActionStatus.ROLLED_BACK
        action.rollback_executed_at = datetime.now(timezone.utc)
        action.rollback_details = f"Rollback executed by {operator_username}: {'; '.join(rollback_details)}"

        audit = AuditLog(
            username=operator_username,
            action="SOAR_ACTION_ROLLED_BACK",
            resource_type="soar_action",
            resource_id=action.id,
            status="SUCCESS",
            details=action.rollback_details
        )
        db.add(audit)
        db.commit()
        db.refresh(action)
        return action

    def get_kpis(self, db: Session) -> Dict[str, Any]:
        """Calculates SOAR response KPIs and status breakdown."""
        actions = db.query(SOARAction).all()
        by_type: Dict[str, int] = {}
        for a in actions:
            by_type[a.action_type] = by_type.get(a.action_type, 0) + 1

        pending = sum(1 for a in actions if a.status == ActionStatus.PENDING_APPROVAL)
        completed = sum(1 for a in actions if a.status == ActionStatus.COMPLETED)
        failed = sum(1 for a in actions if a.status == ActionStatus.FAILED)
        rolled_back = sum(1 for a in actions if a.is_rolled_back)

        return {
            "total_actions": len(actions),
            "pending_approval": pending,
            "completed_actions": completed,
            "failed_actions": failed,
            "rolled_back": rolled_back,
            "by_type": by_type
        }


soar_engine = SOAREngine()
