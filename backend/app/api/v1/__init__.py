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

api_router = APIRouter()

api_router.include_router(health_router, tags=["Health & Diagnostics"])
api_router.include_router(auth_router, tags=["Authentication"])
api_router.include_router(users_router, tags=["User Administration"])
api_router.include_router(audit_router, tags=["Audit Trail"])
api_router.include_router(topologies_router, tags=["Network Simulation & Topologies"])
api_router.include_router(vms_router, tags=["Virtual Machine Integration"])
api_router.include_router(agents_router, tags=["Distributed Linux Agents"])
