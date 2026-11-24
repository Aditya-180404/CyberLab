"""
CyberLab API v1 Package Router
"""
from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.audit import router as audit_router
from app.api.v1.topologies import router as topologies_router
from app.api.v1.vms import router as vms_router
from app.api.v1.agents import router as agents_router
from app.api.v1.assets import router as assets_router
from app.api.v1.siem import router as siem_router
from app.api.v1.soar import router as soar_router
from app.api.v1.digital_twin import router as digital_twin_router
from app.api.v1.purple_team import router as purple_team_router
from app.api.v1.vulnerability import router as vulnerability_router
from app.api.v1.sites import router as sites_router
from app.api.v1.reports import router as reports_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["Health & Diagnostics"])
api_router.include_router(auth_router, tags=["Authentication"])
api_router.include_router(users_router, tags=["User Administration"])
api_router.include_router(audit_router, tags=["Audit Trail"])
api_router.include_router(topologies_router, tags=["Network Simulation & Topologies"])
api_router.include_router(vms_router, tags=["Virtual Machine Integration"])
api_router.include_router(agents_router, tags=["Distributed Linux Agents"])
api_router.include_router(assets_router, tags=["Asset Inventory & Posture"])
api_router.include_router(siem_router, tags=["SIEM & Detection Engine"])
api_router.include_router(soar_router, tags=["SOAR & Incident Response"])
api_router.include_router(digital_twin_router, tags=["Digital Twin & Attack-Path Analysis"])
api_router.include_router(purple_team_router, tags=["Purple-Team & Attack Simulation"])
api_router.include_router(vulnerability_router, tags=["Vulnerability Management & CVEs"])
api_router.include_router(sites_router, tags=["Multi-Site Enterprise Fleet"])
api_router.include_router(reports_router, tags=["Security & Compliance Reports"])




