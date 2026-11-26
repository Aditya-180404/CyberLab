"""
Enterprise Sites REST API Router (Phase 12)
Endpoints for multi-site lifecycle management and distributed telemetry aggregation.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User, UserRole
from app.core.dependencies import get_current_user, require_role
from app.enterprise.site_service import SiteService
from app.schemas.site import SiteCreate, SiteUpdate, SiteResponse, SiteStatsResponse

router = APIRouter(prefix="/sites")


@router.get("", response_model=List[SiteResponse])
def list_sites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all enterprise sites for the current organization."""
    service = SiteService(db, current_user.organization_id)
    return service.list_sites()


@router.get("/stats", response_model=List[SiteStatsResponse])
def get_sites_with_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all enterprise sites with live aggregated fleet stats."""
    service = SiteService(db, current_user.organization_id)
    return service.get_sites_with_stats()


@router.post("", response_model=SiteResponse)
def create_site(
    site_in: SiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.SOC_MANAGER]))
):
    """Register a new remote site in the enterprise organization."""
    service = SiteService(db, current_user.organization_id)
    return service.create_site(site_in)


@router.put("/{site_id}", response_model=SiteResponse)
def update_site(
    site_id: str,
    site_in: SiteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.SOC_MANAGER]))
):
    """Update metadata and status for a site."""
    try:
        service = SiteService(db, current_user.organization_id)
        return service.update_site(site_id, site_in)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))


@router.delete("/{site_id}")
def delete_site(
    site_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.SOC_MANAGER]))
):
    """Delete a site and unlink associated assets."""
    try:
        service = SiteService(db, current_user.organization_id)
        service.delete_site(site_id)
        return {"status": "SUCCESS", "message": f"Site '{site_id}' deleted."}
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
