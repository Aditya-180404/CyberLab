"""
Enterprise Multi-Site Service (Phase 12)
Manages remote sites, subnets, and aggregates distributed fleet metrics.
"""
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.site import Site
from app.models.asset import Asset
from app.models.agent import Agent, AgentStatus
from app.models.siem import SecurityIncident, IncidentStatus
from app.models.vulnerability import AssetVulnerability, Vulnerability, VulnerabilityStatus, VulnerabilitySeverity
from app.schemas.site import SiteCreate, SiteUpdate, SiteResponse, SiteStatsResponse


class SiteService:
    def __init__(self, db: Session, organization_id: str):
        self.db = db
        self.organization_id = organization_id

    def list_sites(self) -> List[Site]:
        """Returns all registered enterprise sites for the organization."""
        sites = self.db.query(Site).filter(Site.organization_id == self.organization_id).all()
        if not sites:
            # Auto-seed default site if none exists
            default_site = Site(
                id=f"site-{str(uuid.uuid4())[:8]}",
                organization_id=self.organization_id,
                name="Primary CyberLab HQ / Kali Node",
                description="Central on-premise security operations center and virtualization cluster.",
                location="Primary Headquarters (Local Kali)",
                status="ONLINE",
                ip_range="10.10.0.0/16"
            )
            self.db.add(default_site)
            self.db.commit()
            self.db.refresh(default_site)
            sites = [default_site]
        return sites

    def get_sites_with_stats(self) -> List[SiteStatsResponse]:
        """Calculates live fleet metrics aggregated across sites."""
        sites = self.list_sites()
        stats: List[SiteStatsResponse] = []

        total_sites = len(sites)

        for site in sites:
            # Query assets assigned to this site, or all assets if only one site exists
            if total_sites == 1:
                assets = self.db.query(Asset).filter(Asset.organization_id == self.organization_id).all()
            else:
                assets = self.db.query(Asset).filter(
                    Asset.organization_id == self.organization_id,
                    Asset.site_id == site.id
                ).all()

            total_assets = len(assets)
            asset_ids = [a.id for a in assets]

            # Active / Online agents
            active_agents = self.db.query(Agent).filter(
                Agent.organization_id == self.organization_id,
                Agent.status == AgentStatus.ONLINE
            ).count()

            # Open incidents
            open_incidents = self.db.query(SecurityIncident).filter(
                SecurityIncident.organization_id == self.organization_id,
                SecurityIncident.status.in_([IncidentStatus.OPEN, IncidentStatus.ACTIVE])
            ).count()

            # Critical vulnerabilities
            crit_vulns = 0
            if asset_ids:
                crit_vulns = self.db.query(AssetVulnerability).join(Vulnerability).filter(
                    AssetVulnerability.asset_id.in_(asset_ids),
                    AssetVulnerability.status == VulnerabilityStatus.OPEN,
                    Vulnerability.severity == VulnerabilitySeverity.CRITICAL
                ).count()

            # Average risk score
            avg_risk = sum(a.risk_score for a in assets) / max(1, total_assets) if total_assets > 0 else 0.0

            stats.append(SiteStatsResponse(
                site_id=site.id,
                name=site.name,
                location=site.location,
                status=site.status or "ONLINE",
                total_assets=total_assets,
                active_agents=active_agents,
                open_incidents=open_incidents,
                critical_vulnerabilities=crit_vulns,
                average_risk_score=round(avg_risk, 1)
            ))

        return stats

    def create_site(self, site_in: SiteCreate) -> Site:
        """Registers a new remote site in the enterprise organization."""
        site = Site(
            id=f"site-{str(uuid.uuid4())[:8]}",
            organization_id=self.organization_id,
            name=site_in.name,
            description=site_in.description,
            location=site_in.location or "Branch Office / Cloud VPC",
            status="ONLINE",
            ip_range=site_in.ip_range
        )
        self.db.add(site)
        self.db.commit()
        self.db.refresh(site)
        return site

    def update_site(self, site_id: str, site_in: SiteUpdate) -> Site:
        """Updates metadata and status for a site."""
        site = self.db.query(Site).filter(
            Site.id == site_id,
            Site.organization_id == self.organization_id
        ).first()
        if not site:
            raise ValueError(f"Site '{site_id}' not found.")

        if site_in.name is not None:
            site.name = site_in.name
        if site_in.description is not None:
            site.description = site_in.description
        if site_in.location is not None:
            site.location = site_in.location
        if site_in.status is not None:
            site.status = site_in.status
        if site_in.ip_range is not None:
            site.ip_range = site_in.ip_range

        self.db.commit()
        self.db.refresh(site)
        return site

    def delete_site(self, site_id: str):
        """Removes an enterprise site and unlinks associated assets."""
        site = self.db.query(Site).filter(
            Site.id == site_id,
            Site.organization_id == self.organization_id
        ).first()
        if not site:
            raise ValueError(f"Site '{site_id}' not found.")

        # Unlink assets
        self.db.query(Asset).filter(Asset.site_id == site_id).update({"site_id": None})
        self.db.delete(site)
        self.db.commit()
