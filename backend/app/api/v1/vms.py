"""
Virtual Machine Management API Router
"""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.vm import VirtualMachine
from app.models.audit import AuditLog
from app.schemas.vm import (
    VMResponse, VMRegisterRequest, VMDiscoverRequest, VMPowerRequest, VMAssociateSegmentRequest,
    VMDiscoveryResult, NetworkAdapterInfo
)
from app.core.dependencies import get_current_user, require_role
from app.vm.manager import vm_manager
from app.vm.vmx_parser import VMXParser

router = APIRouter()


def _format_vm_response(vm: VirtualMachine) -> VMResponse:
    adapters_raw = json.loads(vm.network_adapters_json or "[]")
    adapters = [NetworkAdapterInfo(**a) for a in adapters_raw]
    return VMResponse(
        id=vm.id,
        organization_id=vm.organization_id,
        name=vm.name,
        hypervisor_type=vm.hypervisor_type,
        config_path=vm.config_path,
        power_state=vm.power_state,
        os_type=vm.os_type,
        vcpus=vm.vcpus,
        memory_mb=vm.memory_mb,
        network_adapters=adapters,
        attached_segment_id=vm.attached_segment_id,
        is_vulnerable_target=vm.is_vulnerable_target,
        safety_warning=vm.safety_warning,
        created_at=vm.created_at,
        updated_at=vm.updated_at
    )


@router.get("/vms", response_model=List[VMResponse])
def list_vms(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists registered virtual machines in the user's organization."""
    query = db.query(VirtualMachine)
    if current_user.role != UserRole.SUPER_ADMIN and current_user.organization_id:
        query = query.filter(VirtualMachine.organization_id == current_user.organization_id)
    vms = query.offset(skip).limit(limit).all()
    vms = vm_manager.sync_running_states(db, vms)
    return [_format_vm_response(vm) for vm in vms]


@router.post("/vms/discover", response_model=VMDiscoveryResult)
def discover_vms(
    payload: Optional[VMDiscoverRequest] = None,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.SOC_MANAGER])),
    db: Session = Depends(get_db)
):
    """Scans host filesystem for VMware .vmx configurations and syncs them to inventory."""
    org_id = current_user.organization_id or "default-org"
    custom_paths = payload.custom_paths if payload else None
    res = vm_manager.discover_local_vms(db, org_id, custom_paths)
    return VMDiscoveryResult(
        discovered_count=res["discovered_count"],
        registered_vms=[_format_vm_response(vm) for vm in res["registered_vms"]],
        scanned_paths=res["scanned_paths"]
    )


@router.post("/vms/register", response_model=VMResponse, status_code=status.HTTP_201_CREATED)
def register_vm(
    payload: VMRegisterRequest,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.SOC_MANAGER])),
    db: Session = Depends(get_db)
):
    """Manually registers a single .vmx virtual machine file path."""
    try:
        meta = VMXParser.parse_vmx(payload.config_path)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"VMX file not found: {payload.config_path}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to parse VMX: {str(e)}")

    existing = db.query(VirtualMachine).filter(VirtualMachine.config_path == payload.config_path).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This VM is already registered.")

    vm = VirtualMachine(
        organization_id=current_user.organization_id or "default-org",
        name=payload.name or meta["name"],
        hypervisor_type="vmware_workstation",
        config_path=payload.config_path,
        power_state="STOPPED",
        os_type=meta["os_type"],
        vcpus=meta["vcpus"],
        memory_mb=meta["memory_mb"],
        network_adapters_json=json.dumps(meta["network_adapters"]),
        is_vulnerable_target=payload.is_vulnerable_target or meta["is_vulnerable_target"],
        safety_warning=meta["safety_warning"]
    )
    db.add(vm)
    db.commit()
    db.refresh(vm)

    return _format_vm_response(vm)


@router.get("/vms/{vm_id}", response_model=VMResponse)
def get_vm(
    vm_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves operational details and network adapter inspection for a virtual machine."""
    vm = db.query(VirtualMachine).filter(VirtualMachine.id == vm_id).first()
    if not vm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Virtual machine not found")
    vm_manager.sync_running_states(db, [vm])
    return _format_vm_response(vm)


@router.post("/vms/{vm_id}/power", response_model=VMResponse)
def power_vm(
    vm_id: str,
    payload: VMPowerRequest,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.SOC_MANAGER])),
    db: Session = Depends(get_db)
):
    """Executes start, stop, reset, or suspend operations on a virtual machine."""
    try:
        updated_vm = vm_manager.execute_power_action(
            db, vm_id, payload.action, payload.mode, current_user.username
        )
        return _format_vm_response(updated_vm)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Hypervisor error: {str(e)}")


@router.post("/vms/{vm_id}/associate", response_model=VMResponse)
def associate_vm_to_segment(
    vm_id: str,
    payload: VMAssociateSegmentRequest,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.NETWORK_ENGINEER])),
    db: Session = Depends(get_db)
):
    """Associates a VM with a simulated CyberLab virtual bridge segment."""
    try:
        updated_vm = vm_manager.associate_segment(db, vm_id, payload.segment_id, current_user.username)
        return _format_vm_response(updated_vm)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
