"""
Purple-Team Validation & Attack Simulation Models (Phase 9)
Tracks atomic testing scenarios, safe execution records, detection correlation,
and defensive coverage gap metrics.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base


class SimulationStatus:
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

    ALL = [SCHEDULED, RUNNING, COMPLETED, FAILED]


class DetectionStatus:
    DETECTED = "DETECTED"
    MISSED = "MISSED"
    BLOCKED = "BLOCKED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"

    ALL = [DETECTED, MISSED, BLOCKED, PENDING_VERIFICATION]


class SimulationScenario(Base):
    __tablename__ = "simulation_scenarios"

    id = Column(String(50), primary_key=True)  # e.g. scen-t1082-sysinfo
    name = Column(String(100), nullable=False)
    mitre_tactic = Column(String(50), nullable=False, index=True)
    mitre_technique_id = Column(String(20), nullable=False, index=True)
    mitre_technique_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20), default="MEDIUM", nullable=False)
    safe_payload_type = Column(String(50), default="BENIGN_COMMAND", nullable=False)
    command_template = Column(Text, nullable=True)
    expected_detection_rule = Column(String(100), nullable=True)
    is_atomic = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    executions = relationship("SimulationExecution", back_populates="scenario", cascade="all, delete-orphan")


class SimulationExecution(Base):
    __tablename__ = "simulation_executions"

    id = Column(String(36), primary_key=True, default=lambda: f"exec-{str(uuid.uuid4())[:8]}")
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    scenario_id = Column(String(50), ForeignKey("simulation_scenarios.id", ondelete="CASCADE"), nullable=False)
    target_asset_id = Column(String(36), ForeignKey("assets.id", ondelete="SET NULL"), nullable=True)
    target_name = Column(String(100), nullable=True)
    executed_by = Column(String(50), default="system", nullable=False)
    status = Column(String(30), default=SimulationStatus.COMPLETED, nullable=False)
    executed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    execution_log = Column(Text, nullable=True)
    telemetry_generated = Column(Text, nullable=True)

    # Relationships
    scenario = relationship("SimulationScenario", back_populates="executions")
    target_asset = relationship("Asset")
    validation_result = relationship("ValidationResult", back_populates="execution", uselist=False, cascade="all, delete-orphan")


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(String(36), primary_key=True, default=lambda: f"val-{str(uuid.uuid4())[:8]}")
    execution_id = Column(String(36), ForeignKey("simulation_executions.id", ondelete="CASCADE"), nullable=False, unique=True)
    detection_status = Column(String(30), default=DetectionStatus.PENDING_VERIFICATION, nullable=False)
    matched_alert_id = Column(String(36), ForeignKey("security_alerts.id", ondelete="SET NULL"), nullable=True)
    matched_rule_id = Column(String(100), nullable=True)
    detection_latency_seconds = Column(Float, default=0.0, nullable=False)
    verification_details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    execution = relationship("SimulationExecution", back_populates="validation_result")
    matched_alert = relationship("SecurityAlert")
