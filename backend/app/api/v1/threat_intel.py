"""
Threat Intelligence & Deception API Router
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.siem import EventCategory, EventSeverity
from app.core.dependencies import get_current_user, require_role
from app.threat_intel.engine import ThreatIntelEngine
from app.siem.engine import siem_engine
from app.schemas.siem import SecurityEventCreate
from app.schemas.threat_intel import (
    ThreatIOCCreate, ThreatIOCResponse,
    DeceptionTrapCreate, DeceptionTrapResponse,
)

router = APIRouter(prefix="/threat-intel")


@router.get("/iocs", response_model=List[ThreatIOCResponse])
def list_iocs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists active Threat Intelligence IOCs (IPs, Domains, Hashes)."""
    engine = ThreatIntelEngine(db, current_user.organization_id or "default-org")
    return engine.list_iocs()


@router.post("/iocs", response_model=ThreatIOCResponse, status_code=status.HTTP_201_CREATED)
def add_ioc(
    payload: ThreatIOCCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.SOC_MANAGER, UserRole.SOC_ANALYST])),
):
    """Adds an indicator of compromise (IOC) to the live correlation feed."""
    engine = ThreatIntelEngine(db, current_user.organization_id or "default-org")
    return engine.add_ioc(payload)


@router.delete("/iocs/{ioc_id}")
def delete_ioc(
    ioc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.SOC_MANAGER])),
):
    """Removes an IOC from the threat intelligence feed."""
    engine = ThreatIntelEngine(db, current_user.organization_id or "default-org")
    try:
        engine.delete_ioc(ioc_id)
        return {"status": "deleted", "id": ioc_id}
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))


@router.get("/traps", response_model=List[DeceptionTrapResponse])
def list_deception_traps(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists active honeypot and canary deception traps."""
    engine = ThreatIntelEngine(db, current_user.organization_id or "default-org")
    return engine.list_traps()


@router.post("/traps", response_model=DeceptionTrapResponse, status_code=status.HTTP_201_CREATED)
def create_deception_trap(
    payload: DeceptionTrapCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.SOC_MANAGER, UserRole.SOC_ANALYST])),
):
    """Creates a new deception trap or canary file monitor."""
    engine = ThreatIntelEngine(db, current_user.organization_id or "default-org")
    return engine.add_trap(payload)


@router.post("/traps/{trap_id}/trigger", response_model=DeceptionTrapResponse)
def trigger_deception_trap(
    trap_id: str,
    source_ip: str = "192.168.1.188",
    hostname: str = "decoy-sensor",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.SOC_MANAGER, UserRole.SOC_ANALYST])),
):
    """Records a deception trap hit and emits a CRITICAL SIEM alert."""
    org_id = current_user.organization_id or "default-org"
    engine = ThreatIntelEngine(db, org_id)
    traps = [t for t in engine.list_traps() if t.id == trap_id]
    if not traps:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deception trap not found")
    trap = engine.mark_trap_triggered(traps[0])

    evt = SecurityEventCreate(
        category=EventCategory.FILE_INTEGRITY if trap.trap_type == "CANARY_FILE" else EventCategory.NETWORK_CONNECTION,
        severity=EventSeverity.CRITICAL,
        action="DECEPTION_TRAP_TRIGGERED",
        message=f"DECEPTION_TRAP_TRIGGERED: '{trap.name}' ({trap.target_indicator}) touched by {source_ip}",
        hostname=hostname,
        source_ip=source_ip,
        mitre_tactic="Discovery",
        mitre_technique_id="T1083",
        raw_data={"trap_id": trap.id, "trap_type": trap.trap_type, "indicator": trap.target_indicator},
    )
    siem_engine.ingest_event(db, evt, organization_id=org_id)
    return trap
