"""
Unified Asset Inventory API Router (Phase 5)
Provides search, filtering, automated multi-source synchronization, and risk posture inspection.
"""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.asset import Asset, AssetType, AssetCriticality, AssetStatus
from app.models.audit import AuditLog
from app.schemas.asset import (
    AssetResponse, AssetDetailResponse, AssetCriticalityUpdateRequest,
    AssetSyncResult, AssetInventoryKPIs
)
from app.inventory.asset_manager import asset_manager
from app.core.dependencies import get_current_user, require_role

router = APIRouter()


def _format_asset(a: Asset) -> AssetResponse:
    """Helper to deserialize stored JSON structures into typed Pydantic responses."""
    return AssetResponse(
        id=a.id,
        organization_id=a.organization_id,
        site_id=a.site_id,
        name=a.name,
        asset_type=a.asset_type,
        ip_addresses=json.loads(a.ip_addresses_json or "[]"),
        mac_addresses=json.loads(a.mac_addresses_json or "[]"),
        os_family=a.os_family,
        os_version=a.os_version,
        kernel_version=a.kernel_version,
        criticality=a.criticality,
        risk_score=a.risk_score,
        exposure=a.exposure,
        status=a.status,
        virtual_machine_id=a.virtual_machine_id,
        agent_id=a.agent_id,
        network_device_id=a.network_device_id,
        hardware_specs=json.loads(a.hardware_specs_json or "{}") if a.hardware_specs_json else None,
        services=json.loads(a.services_json or "[]") if a.services_json else None,
        software_inventory=json.loads(a.software_inventory_json or "[]") if a.software_inventory_json else None,
        security_tags=json.loads(a.security_tags_json or "[]"),
        last_seen=a.last_seen,
        created_at=a.created_at,
        updated_at=a.updated_at
    )


@router.get("/assets", response_model=List[AssetResponse])
def list_assets(
    skip: int = 0,
    limit: int = 50,
    asset_type: Optional[str] = Query(None, description="Filter by AssetType (VIRTUAL_MACHINE, AGENT_HOST, SIMULATED_DEVICE)"),
    criticality: Optional[str] = Query(None, description="Filter by criticality (LOW, MEDIUM, HIGH, CRITICAL)"),
    min_risk: Optional[int] = Query(None, ge=0, le=100, description="Minimum risk score threshold"),
    search: Optional[str] = Query(None, description="Search by asset name or IP"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves unified asset inventory with multi-criteria filtering."""
    query = db.query(Asset)

    if asset_type:
        query = query.filter(Asset.asset_type == asset_type)
    if criticality:
        query = query.filter(Asset.criticality == criticality)
    if min_risk is not None:
        query = query.filter(Asset.risk_score >= min_risk)
    if search:
        pattern = f"%{search}%"
        query = query.filter((Asset.name.ilike(pattern)) | (Asset.ip_addresses_json.ilike(pattern)))

    assets = query.order_by(Asset.risk_score.desc()).offset(skip).limit(limit).all()
    return [_format_asset(a) for a in assets]


@router.get("/assets/kpis", response_model=AssetInventoryKPIs)
def get_asset_kpis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns aggregated fleet metrics, risk averages, and asset category breakdown."""
    return asset_manager.get_kpis(db)


@router.post("/assets/sync", response_model=AssetSyncResult)
def synchronize_assets(
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.SOC_MANAGER, UserRole.SOC_ANALYST, UserRole.NETWORK_ENGINEER])),
    db: Session = Depends(get_db)
):
    """Synchronizes registered VMs, Agents, and Simulated Devices into unified Asset records."""
    result = asset_manager.sync_all(db)

    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="ASSET_INVENTORY_SYNC",
        resource_type="asset_inventory",
        status="SUCCESS",
        details=f"User '{current_user.username}' synchronized asset inventory ({result['total_synced']} entities)"
    )
    db.add(audit)
    db.commit()

    return AssetSyncResult(**result)


@router.get("/assets/{asset_id}", response_model=AssetDetailResponse)
def get_asset_detail(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns deep details for a single asset including underlying source telemetry."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    base = _format_asset(asset)

    vm_data = None
    if asset.virtual_machine:
        vm = asset.virtual_machine
        vm_data = {
            "id": vm.id,
            "name": vm.name,
            "power_state": vm.power_state,
            "config_path": vm.config_path,
            "is_vulnerable_target": vm.is_vulnerable_target,
            "adapters": json.loads(vm.network_adapters_json or "[]")
        }

    agent_data = None
    if asset.agent:
        ag = asset.agent
        agent_data = {
            "id": ag.id,
            "hostname": ag.hostname,
            "status": ag.status,
            "agent_version": ag.agent_version,
            "last_heartbeat": ag.last_heartbeat.isoformat() if ag.last_heartbeat else None
        }

    device_data = None
    if asset.network_device:
        dev = asset.network_device
        device_data = {
            "id": dev.id,
            "name": dev.name,
            "device_type": dev.device_type,
            "status": dev.status
        }

    return AssetDetailResponse(
        **base.model_dump(),
        vm_details=vm_data,
        agent_details=agent_data,
        device_details=device_data
    )


@router.put("/assets/{asset_id}/criticality", response_model=AssetResponse)
def update_asset_criticality(
    asset_id: str,
    payload: AssetCriticalityUpdateRequest,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.SOC_MANAGER, UserRole.SOC_ANALYST])),
    db: Session = Depends(get_db)
):
    """Allows authorized SOC analysts to reclassify asset business sensitivity or network exposure."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    old_crit = asset.criticality
    asset.criticality = payload.criticality
    if payload.exposure:
        asset.exposure = payload.exposure

    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="ASSET_CRITICALITY_UPDATED",
        resource_type="asset",
        resource_id=asset.id,
        status="SUCCESS",
        details=f"Analyst '{current_user.username}' changed criticality of asset '{asset.name}' from {old_crit} to {payload.criticality}"
    )
    db.add(audit)
    db.commit()
    db.refresh(asset)

    return _format_asset(asset)
