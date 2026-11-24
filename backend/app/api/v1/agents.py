"""
Distributed Linux Agent API Router
Handles agent registration, heartbeats, telemetry ingestion, and SOAR response controls.
"""
import json
import secrets
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.agent import Agent, AgentStatus, AgentTelemetry
from app.models.audit import AuditLog
from app.schemas.agent import (
    AgentRegisterRequest, AgentRegisterResponse, AgentHeartbeatRequest, AgentHeartbeatResponse,
    AgentTelemetryBatch, AgentResponse, AgentDetailResponse
)
from app.core.dependencies import get_current_user, require_role
from app.core.security import get_password_hash, verify_password

router = APIRouter()

DEFAULT_POLICY = {
    "telemetry_interval_sec": 15,
    "fim_monitored_paths": [
        "/etc/passwd",
        "/etc/shadow",
        "/etc/sudoers",
        "/etc/ssh/sshd_config",
        "/etc/hosts"
    ],
    "monitor_processes": True,
    "monitor_sockets": True,
    "monitor_auth_logs": True
}


def _verify_agent_token(
    authorization: Optional[str] = Header(None),
    x_agent_id: Optional[str] = Header(None, alias="X-CyberLab-Agent-ID"),
    db: Session = Depends(get_db)
) -> Agent:
    """Authenticates the agent using its Bearer token and Agent ID header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or malformed Bearer token")

    token = authorization.split(" ", 1)[1]
    if not x_agent_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing X-CyberLab-Agent-ID header")

    agent = db.query(Agent).filter(Agent.id == x_agent_id).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent identity not registered")

    if agent.status == AgentStatus.REVOKED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agent credentials have been revoked")

    if not verify_password(token, agent.agent_token_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid agent authentication token")

    return agent


def _format_agent_response(agent: Agent) -> AgentResponse:
    specs = json.loads(agent.hardware_specs_json or "{}")
    # Mark offline if heartbeat missed for > 35 seconds
    st = agent.status
    last_hb = agent.last_heartbeat
    if last_hb:
        if last_hb.tzinfo is None:
            last_hb = last_hb.replace(tzinfo=timezone.utc)
        if st == AgentStatus.ONLINE and (datetime.now(timezone.utc) - last_hb) > timedelta(seconds=35):
            st = AgentStatus.OFFLINE

    return AgentResponse(
        id=agent.id,
        organization_id=agent.organization_id,
        hostname=agent.hostname,
        ip_address=agent.ip_address,
        os_type=agent.os_type,
        os_release=agent.os_release,
        kernel_version=agent.kernel_version,
        agent_version=agent.agent_version,
        status=st,
        last_heartbeat=agent.last_heartbeat,
        heartbeat_interval_sec=agent.heartbeat_interval_sec,
        hardware_specs=specs,
        created_at=agent.created_at,
        updated_at=agent.updated_at
    )


@router.post("/agents/register", response_model=AgentRegisterResponse, status_code=status.HTTP_201_CREATED)
def register_agent(payload: AgentRegisterRequest, db: Session = Depends(get_db)):
    """Registers an autonomous Linux agent and generates unique cryptographic credentials."""
    raw_token = f"cla_{secrets.token_urlsafe(32)}"
    token_hash = get_password_hash(raw_token)

    agent_id = f"cl-agent-{secrets.token_hex(4)}"

    # Default to first organization or baseline
    org_id = "default-org"

    agent = Agent(
        id=agent_id,
        organization_id=org_id,
        hostname=payload.hostname,
        ip_address=payload.ip_address,
        os_type=payload.os_type,
        os_release=payload.os_release,
        kernel_version=payload.kernel_version,
        agent_version=payload.agent_version,
        status=AgentStatus.ONLINE,
        agent_token_hash=token_hash,
        heartbeat_interval_sec=10,
        hardware_specs_json=json.dumps(payload.hardware_specs or {}),
        policy_json=json.dumps(DEFAULT_POLICY),
        pending_commands_json=json.dumps([])
    )
    db.add(agent)

    audit = AuditLog(
        username="agent-installer",
        action="AGENT_REGISTERED",
        resource_type="agent",
        resource_id=agent_id,
        status="SUCCESS",
        ip_address=payload.ip_address,
        details=f"Registered agent on host '{payload.hostname}' ({payload.os_release})"
    )
    db.add(audit)
    db.commit()
    db.refresh(agent)

    return AgentRegisterResponse(
        agent_id=agent.id,
        agent_token=raw_token,
        heartbeat_interval_sec=agent.heartbeat_interval_sec,
        policy=DEFAULT_POLICY
    )


@router.post("/agents/heartbeat", response_model=AgentHeartbeatResponse)
def agent_heartbeat(
    payload: AgentHeartbeatRequest,
    agent: Agent = Depends(_verify_agent_token),
    db: Session = Depends(get_db)
):
    """Processes recurring agent heartbeat, updates activity timestamp, and returns pending commands."""
    agent.last_heartbeat = datetime.now(timezone.utc)
    if agent.status == AgentStatus.OFFLINE:
        agent.status = AgentStatus.ONLINE

    pending_cmds = json.loads(agent.pending_commands_json or "[]")
    # Clear dispatched commands
    agent.pending_commands_json = json.dumps([])

    db.commit()

    return AgentHeartbeatResponse(
        status=agent.status,
        pending_commands=pending_cmds,
        policy_updated=False,
        policy=json.loads(agent.policy_json or "{}")
    )


@router.post("/agents/telemetry", status_code=status.HTTP_200_OK)
def ingest_telemetry(
    payload: AgentTelemetryBatch,
    agent: Agent = Depends(_verify_agent_token),
    db: Session = Depends(get_db)
):
    """Ingests batched host telemetry: active sockets, running processes, auth events, FIM alerts."""
    record = AgentTelemetry(
        agent_id=agent.id,
        cpu_pct=payload.cpu_pct,
        memory_pct=payload.memory_pct,
        disk_pct=payload.disk_pct,
        network_connections_json=json.dumps(payload.network_connections or []),
        processes_json=json.dumps(payload.processes or []),
        auth_events_json=json.dumps(payload.auth_events or []),
        fim_alerts_json=json.dumps(payload.fim_alerts or [])
    )
    db.add(record)
    agent.last_heartbeat = datetime.now(timezone.utc)
    db.commit()

    return {"status": "ingested", "records": len(payload.processes or [])}


@router.get("/agents", response_model=List[AgentResponse])
def list_agents(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists registered agent fleet with live health and connectivity states."""
    agents = db.query(Agent).offset(skip).limit(limit).all()
    return [_format_agent_response(a) for a in agents]


@router.get("/agents/{agent_id}", response_model=AgentDetailResponse)
def get_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves single agent metadata and recent telemetry snapshot."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    base = _format_agent_response(agent)
    pending = json.loads(agent.pending_commands_json or "[]")

    latest_rec = agent.telemetry[0] if agent.telemetry else None
    telemetry_data = None
    if latest_rec:
        telemetry_data = {
            "timestamp": latest_rec.created_at,
            "cpu_pct": latest_rec.cpu_pct,
            "memory_pct": latest_rec.memory_pct,
            "disk_pct": latest_rec.disk_pct,
            "network_connections": json.loads(latest_rec.network_connections_json or "[]"),
            "processes_count": len(json.loads(latest_rec.processes_json or "[]")),
            "fim_alerts": json.loads(latest_rec.fim_alerts_json or "[]")
        }

    return AgentDetailResponse(
        **base.model_dump(),
        pending_commands=pending,
        latest_telemetry=telemetry_data
    )


@router.post("/agents/{agent_id}/isolate", response_model=AgentResponse)
def isolate_endpoint(
    agent_id: str,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.SOC_MANAGER, UserRole.SOC_ANALYST])),
    db: Session = Depends(get_db)
):
    """Queues an authorized isolation directive for the agent."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    pending = json.loads(agent.pending_commands_json or "[]")
    if "ISOLATE" not in pending:
        pending.append("ISOLATE")
        agent.pending_commands_json = json.dumps(pending)

    agent.status = AgentStatus.ISOLATED

    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="AGENT_ISOLATED",
        resource_type="agent",
        resource_id=agent.id,
        status="SUCCESS",
        details=f"Analyst {current_user.username} ordered network isolation for host '{agent.hostname}'"
    )
    db.add(audit)
    db.commit()
    db.refresh(agent)
    return _format_agent_response(agent)


@router.post("/agents/{agent_id}/restore", response_model=AgentResponse)
def restore_endpoint(
    agent_id: str,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.SOC_MANAGER, UserRole.SOC_ANALYST])),
    db: Session = Depends(get_db)
):
    """Queues a restoration directive to reverse network isolation."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    pending = json.loads(agent.pending_commands_json or "[]")
    if "RESTORE" not in pending:
        pending.append("RESTORE")
        agent.pending_commands_json = json.dumps(pending)

    agent.status = AgentStatus.ONLINE

    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="AGENT_RESTORED",
        resource_type="agent",
        resource_id=agent.id,
        status="SUCCESS",
        details=f"Analyst {current_user.username} restored normal network policy for host '{agent.hostname}'"
    )
    db.add(audit)
    db.commit()
    db.refresh(agent)
    return _format_agent_response(agent)


@router.post("/agents/{agent_id}/revoke", response_model=AgentResponse)
def revoke_agent(
    agent_id: str,
    current_user: User = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN])),
    db: Session = Depends(get_db)
):
    """Revokes agent credentials immediately, cutting off further telemetry or command reception."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    agent.status = AgentStatus.REVOKED
    # Scramble token hash so token can never be verified
    agent.agent_token_hash = get_password_hash(secrets.token_hex(32))

    audit = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="AGENT_CREDENTIALS_REVOKED",
        resource_type="agent",
        resource_id=agent.id,
        status="SUCCESS",
        details=f"Revoked credentials for agent '{agent.id}' ({agent.hostname})"
    )
    db.add(audit)
    db.commit()
    db.refresh(agent)
    return _format_agent_response(agent)
