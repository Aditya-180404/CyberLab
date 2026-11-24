"""
SOAR (Security Orchestration, Automation and Response) Models (Phase 7)
Stores playbooks, response actions, human-in-the-loop approvals, and verification logs.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database.session import Base


class ActionType:
    ISOLATE_HOST = "ISOLATE_HOST"
    RESTORE_HOST = "RESTORE_HOST"
    BLOCK_IP = "BLOCK_IP"
    UNBLOCK_IP = "UNBLOCK_IP"
    SUSPEND_VM = "SUSPEND_VM"
    REVOKE_CREDENTIALS = "REVOKE_CREDENTIALS"

    ALL = [ISOLATE_HOST, RESTORE_HOST, BLOCK_IP, UNBLOCK_IP, SUSPEND_VM, REVOKE_CREDENTIALS]


class ActionStatus:
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"

    ALL = [PENDING_APPROVAL, APPROVED, REJECTED, EXECUTING, COMPLETED, FAILED, ROLLED_BACK]


class SOARPlaybook(Base):
    __tablename__ = "soar_playbooks"

    id = Column(String(50), primary_key=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    trigger_event = Column(String(50), default="ON_DEMAND", nullable=False)
    requires_approval = Column(Boolean, default=True, nullable=False)
    action_type = Column(String(50), nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    actions = relationship("SOARAction", back_populates="playbook")


class SOARAction(Base):
    __tablename__ = "soar_actions"

    id = Column(String(36), primary_key=True, default=lambda: f"soar-act-{str(uuid.uuid4())[:8]}")
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    playbook_id = Column(String(50), ForeignKey("soar_playbooks.id", ondelete="SET NULL"), nullable=True)

    action_type = Column(String(50), nullable=False, index=True)
    status = Column(String(30), default=ActionStatus.PENDING_APPROVAL, nullable=False, index=True)

    # Target Context
    target_type = Column(String(30), default="ASSET", nullable=False)  # ASSET, AGENT, VM, IP
    target_id = Column(String(100), nullable=False, index=True)
    target_name = Column(String(100), nullable=True)
    incident_id = Column(String(36), ForeignKey("security_incidents.id", ondelete="SET NULL"), nullable=True)

    # Human-in-the-loop Governance
    requested_by = Column(String(100), default="system", nullable=False)
    approved_by = Column(String(100), nullable=True)
    rejection_reason = Column(String(255), nullable=True)

    # Execution & Verification
    executed_at = Column(DateTime, nullable=True)
    verified = Column(Boolean, default=False, nullable=False)
    verification_details = Column(Text, nullable=True)

    # Rollback Capability
    rollback_supported = Column(Boolean, default=True, nullable=False)
    is_rolled_back = Column(Boolean, default=False, nullable=False)
    rollback_executed_at = Column(DateTime, nullable=True)
    rollback_details = Column(Text, nullable=True)

    # Logs & Metadata
    parameters_json = Column(Text, nullable=True)
    output_log = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    playbook = relationship("SOARPlaybook", back_populates="actions")
    incident = relationship("SecurityIncident")
