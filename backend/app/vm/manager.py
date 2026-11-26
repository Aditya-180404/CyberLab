"""
Virtual Machine Lifecycle & Inventory Manager
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.vm import VirtualMachine, PowerState
from app.models.segment import NetworkSegment
from app.models.audit import AuditLog
from app.vm.vmx_parser import VMXParser
from app.vm.adapter import HypervisorAdapter
from app.vm.vmware_adapter import VMwareWorkstationAdapter

logger = logging.getLogger("cyberlab.vm.manager")


class VMManager:
    DEFAULT_SCAN_PATHS = [
        "/home/ghost/VMware",
        "/run/media/ghost/New Volume",
        "/home/ghost/VirtualBox VMs",
    ]

    def __init__(self, adapter: Optional[HypervisorAdapter] = None):
        self.adapter = adapter or VMwareWorkstationAdapter()

    def set_adapter(self, adapter: HypervisorAdapter):
        self.adapter = adapter

    def sync_running_states(self, db: Session, vms: List[VirtualMachine]) -> List[VirtualMachine]:
        """Syncs DB power_state for VMs against the live hypervisor inventory."""
        if not vms:
            return vms

        try:
            if hasattr(self.adapter, "try_list_running_vms"):
                running_list = self.adapter.try_list_running_vms()
                if running_list is None:
                    return vms
            else:
                running_list = self.adapter.list_running_vms()
        except Exception as e:
            logger.warning(f"Live VM state sync skipped: {e}")
            return vms

        running_set = {
            os.path.realpath(p) if os.path.exists(p) else p
            for p in running_list
        }

        changed = False
        for vm in vms:
            norm_path = os.path.realpath(vm.config_path) if os.path.exists(vm.config_path) else vm.config_path
            is_running = (norm_path in running_set) or (vm.config_path in running_set)
            if is_running:
                target_state = PowerState.RUNNING
            elif vm.power_state == PowerState.SUSPENDED:
                target_state = PowerState.SUSPENDED
            else:
                target_state = PowerState.STOPPED

            if vm.power_state != target_state:
                vm.power_state = target_state
                changed = True

        if changed:
            db.commit()
            for vm in vms:
                db.refresh(vm)
        return vms

    def discover_local_vms(
        self, db: Session, organization_id: str, custom_paths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Scans filesystem for .vmx files and registers or updates them in the database."""
        paths_to_scan = list(self.DEFAULT_SCAN_PATHS)
        if custom_paths:
            paths_to_scan.extend(custom_paths)

        running_raw = (
            self.adapter.try_list_running_vms()
            if hasattr(self.adapter, "try_list_running_vms")
            else self.adapter.list_running_vms()
        )
        running_known = running_raw is not None
        running_vms = set(running_raw or [])
        discovered_records: List[VirtualMachine] = []

        for root_path in paths_to_scan:
            if not os.path.exists(root_path):
                continue

            for dirpath, _, filenames in os.walk(root_path):
                for filename in filenames:
                    if filename.lower().endswith(".vmx"):
                        full_path = os.path.realpath(os.path.join(dirpath, filename))
                        try:
                            meta = VMXParser.parse_vmx(full_path)
                            is_running = full_path in running_vms

                            # Check if already exists in DB
                            vm = db.query(VirtualMachine).filter(VirtualMachine.config_path == full_path).first()
                            if not vm:
                                vm = VirtualMachine(
                                    organization_id=organization_id,
                                    name=meta["name"],
                                    hypervisor_type="vmware_workstation",
                                    config_path=full_path,
                                    power_state=PowerState.RUNNING if is_running else PowerState.STOPPED,
                                    os_type=meta["os_type"],
                                    vcpus=meta["vcpus"],
                                    memory_mb=meta["memory_mb"],
                                    network_adapters_json=json.dumps(meta["network_adapters"]),
                                    is_vulnerable_target=meta["is_vulnerable_target"],
                                    safety_warning=meta["safety_warning"]
                                )
                                db.add(vm)
                            else:
                                vm.name = meta["name"]
                                vm.vcpus = meta["vcpus"]
                                vm.memory_mb = meta["memory_mb"]
                                vm.network_adapters_json = json.dumps(meta["network_adapters"])
                                vm.is_vulnerable_target = meta["is_vulnerable_target"]
                                vm.safety_warning = meta["safety_warning"]
                                if running_known:
                                    if is_running:
                                        vm.power_state = PowerState.RUNNING
                                    elif vm.power_state != PowerState.SUSPENDED:
                                        vm.power_state = PowerState.STOPPED

                            db.flush()
                            discovered_records.append(vm)
                        except Exception as e:
                            logger.error(f"Error parsing VMX {full_path}: {e}")

        db.commit()
        for vm in discovered_records:
            db.refresh(vm)

        return {
            "discovered_count": len(discovered_records),
            "registered_vms": discovered_records,
            "scanned_paths": paths_to_scan
        }

    def execute_power_action(
        self, db: Session, vm_id: str, action: str, mode: str, username: str
    ) -> VirtualMachine:
        """Executes start, stop, reset, or suspend against target VM with safety validation."""
        vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
        if not vm:
            raise ValueError(f"Virtual Machine {vm_id} not found.")

        # Safety Check: If starting a vulnerable target with bridged adapter, warn
        if action.lower() == "start" and vm.is_vulnerable_target and vm.safety_warning:
            logger.warning(f"Starting vulnerable target {vm.name} with warning: {vm.safety_warning}")

        action_clean = action.lower()
        soft = (mode.lower() == "soft")

        try:
            if action_clean == "start":
                self.adapter.start_vm(vm.config_path)
                vm.power_state = PowerState.RUNNING
            elif action_clean == "stop":
                self.adapter.stop_vm(vm.config_path, soft=soft)
                vm.power_state = PowerState.STOPPED
            elif action_clean == "reset":
                self.adapter.reset_vm(vm.config_path, soft=soft)
                vm.power_state = PowerState.RUNNING
            elif action_clean == "suspend":
                self.adapter.suspend_vm(vm.config_path)
                vm.power_state = PowerState.SUSPENDED
            else:
                raise ValueError(f"Unsupported power action: {action}. Use start, stop, reset, or suspend.")

            audit = AuditLog(
                username=username,
                action=f"VM_POWER_{action.upper()}",
                resource_type="virtual_machine",
                resource_id=vm.id,
                status="SUCCESS",
                details=f"Executed {action} ({mode}) on VM '{vm.name}'"
            )
            db.add(audit)
            db.commit()
            db.refresh(vm)
            return vm

        except Exception as e:
            logger.error(f"Power action {action} failed on VM {vm.name}: {e}")
            audit = AuditLog(
                username=username,
                action=f"VM_POWER_{action.upper()}_FAILED",
                resource_type="virtual_machine",
                resource_id=vm.id,
                status="FAILURE",
                details=str(e)
            )
            db.add(audit)
            db.commit()
            raise

    def associate_segment(
        self, db: Session, vm_id: str, segment_id: Optional[str], username: str
    ) -> VirtualMachine:
        """Associates a VM with a CyberLab simulated network segment."""
        vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
        if not vm:
            raise ValueError(f"Virtual Machine {vm_id} not found.")

        if segment_id:
            seg = db.query(NetworkSegment).filter(NetworkSegment.id == segment_id).first()
            if not seg:
                raise ValueError(f"Network Segment {segment_id} not found.")
            vm.attached_segment_id = segment_id
        else:
            vm.attached_segment_id = None

        audit = AuditLog(
            username=username,
            action="VM_SEGMENT_ASSOCIATED",
            resource_type="virtual_machine",
            resource_id=vm.id,
            status="SUCCESS",
            details=f"Associated VM '{vm.name}' to segment {segment_id}"
        )
        db.add(audit)
        db.commit()
        db.refresh(vm)
        return vm


vm_manager = VMManager()
