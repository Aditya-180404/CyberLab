"""
System Health & Diagnostics Schemas
"""
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel


class PlatformMetrics(BaseModel):
    os: str
    kernel: str
    python: str
    cpu_usage_pct: float
    memory_total_gb: float
    memory_used_gb: float
    memory_usage_pct: float
    disk_total_gb: float
    disk_free_gb: float
    disk_usage_pct: float


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    project_name: str
    tagline: str
    database: str
    platform: PlatformMetrics
    checks: Dict[str, bool]
