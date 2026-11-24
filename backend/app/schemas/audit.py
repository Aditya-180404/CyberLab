"""
Audit Log Schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    id: str
    user_id: Optional[str]
    username: str
    action: str
    resource_type: str
    resource_id: Optional[str]
    status: str
    ip_address: Optional[str]
    details: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
