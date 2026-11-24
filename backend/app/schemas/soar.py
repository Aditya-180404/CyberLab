"""
SOAR Schemas (Phase 7)
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class SOARPlaybookResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    description: str
    trigger_event: str
    requires_approval: bool
    action_type: str
    is_enabled: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SOARActionCreateRequest(BaseModel):
    playbook_id: Optional[str] = None
    action_type: str = Field(..., description="ISOLATE_HOST, RESTORE_HOST, BLOCK_IP, UNBLOCK_IP, SUSPEND_VM, REVOKE_CREDENTIALS")
    target_type: str = Field("ASSET", description="ASSET, AGENT, VM, IP")
    target_id: str = Field(..., min_length=1)
    target_name: Optional[str] = None
    incident_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class SOARActionResponse(BaseModel):
    id: str
    organization_id: str
    playbook_id: Optional[str] = None
    action_type: str
    status: str
    target_type: str
    target_id: str
    target_name: Optional[str] = None
    incident_id: Optional[str] = None
    requested_by: str
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    executed_at: Optional[datetime] = None
    verified: bool
    verification_details: Optional[str] = None
    rollback_supported: bool
    is_rolled_back: bool
    rollback_details: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    output_log: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SOARApprovalDecisionRequest(BaseModel):
    reason: Optional[str] = None


class SOARKPIs(BaseModel):
    total_actions: int
    pending_approval: int
    completed_actions: int
    failed_actions: int
    rolled_back: int
    by_type: Dict[str, int]
