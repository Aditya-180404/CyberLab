"""
Purple-Team Simulation & Validation Engine (Phase 9)
Executes atomic test scenarios against authorized assets, verifies SIEM/EDR detections,
computes defensive efficacy metrics, and identifies MITRE ATT&CK coverage gaps.
"""
import json
import uuid
import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.purple_team import (
    SimulationScenario, SimulationExecution, ValidationResult,
    SimulationStatus, DetectionStatus
)
from app.models.asset import Asset
from app.models.siem import (
    SecurityEvent, SecurityAlert, EventCategory, EventSeverity
)
from app.schemas.purple_team import (
    SimulationScenarioResponse, SimulationExecutionResponse, ValidationResultResponse,
    RunCampaignResponse, MitreCoverageResponse, MitreCoverageItem, PurpleTeamKPIs
)
from app.schemas.siem import SecurityEventCreate
from app.siem.engine import SIEMEngine

# Built-in Library of Safe, Atomic Purple-Team Scenarios
DEFAULT_SCENARIOS = [
    {
        "id": "scen-t1082-sysinfo",
        "name": "System Information Discovery Probe",
        "mitre_tactic": "Discovery",
        "mitre_technique_id": "T1082",
        "mitre_technique_name": "System Information Discovery",
        "description": "Executes harmless system info query ('uname -a') to test telemetry collection.",
        "severity": "LOW",
        "safe_payload_type": "BENIGN_COMMAND",
        "command_template": "uname -a && cat /etc/os-release",
        "expected_detection_rule": None,
        "is_atomic": True
    },
    {
        "id": "scen-t1033-userinfo",
        "name": "User Account Discovery Probe",
        "mitre_tactic": "Discovery",
        "mitre_technique_id": "T1033",
        "mitre_technique_name": "Security Account Manager Discovery",
        "description": "Queries current user identification ('id && whoami') to test account discovery logging.",
        "severity": "LOW",
        "safe_payload_type": "BENIGN_COMMAND",
        "command_template": "id && whoami",
        "expected_detection_rule": None,
        "is_atomic": True
    },
    {
        "id": "scen-t1110-brute-force",
        "name": "SSH Authentication Brute Force Simulation",
        "mitre_tactic": "Credential Access",
        "mitre_technique_id": "T1110",
        "mitre_technique_name": "Brute Force",
        "description": "Simulates 6 failed SSH logon attempts within 10 seconds to validate brute force alerting.",
        "severity": "HIGH",
        "safe_payload_type": "TELEMETRY_INJECTION",
        "command_template": "ssh -o BatchMode=yes invalid_user@<target>",
        "expected_detection_rule": "RULE_AUTH_BRUTE_FORCE",
        "is_atomic": True
    },
    {
        "id": "scen-t1548-sudo-abuse",
        "name": "Privilege Escalation via Sudo Abuse Simulation",
        "mitre_tactic": "Privilege Escalation",
        "mitre_technique_id": "T1548.003",
        "mitre_technique_name": "Sudo and Sudo Caching",
        "description": "Simulates unauthorized execution of interactive root shell via sudo.",
        "severity": "HIGH",
        "safe_payload_type": "TELEMETRY_INJECTION",
        "command_template": "sudo -u root /bin/bash -c 'id'",
        "expected_detection_rule": "RULE_PRIVILEGE_ESCALATION_SUDO",
        "is_atomic": True
    },
    {
        "id": "scen-t1003-shadow-dump",
        "name": "Credential Access: /etc/shadow Canary Access",
        "mitre_tactic": "Credential Access",
        "mitre_technique_id": "T1003.008",
        "mitre_technique_name": "/etc/passwd and /etc/shadow",
        "description": "Simulates read attempt on sensitive authentication file /etc/shadow.",
        "severity": "CRITICAL",
        "safe_payload_type": "CANARY_FILE_CHECK",
        "command_template": "cat /etc/shadow",
        "expected_detection_rule": "RULE_CREDENTIAL_DUMPING_SHADOW",
        "is_atomic": True
    },
    {
        "id": "scen-t1046-port-scan",
        "name": "Network Service Discovery / Port Recon",
        "mitre_tactic": "Discovery",
        "mitre_technique_id": "T1046",
        "mitre_technique_name": "Network Service Discovery",
        "description": "Simulates rapid network connection attempts across 12 ports to trigger recon detection.",
        "severity": "MEDIUM",
        "safe_payload_type": "PORT_PROBE",
        "command_template": "nc -zv <target> 21-80",
        "expected_detection_rule": "RULE_PORT_SCAN_RECON",
        "is_atomic": True
    },
    {
        "id": "scen-t1059-shell-exec",
        "name": "Suspicious Shell Base64 Command Execution",
        "mitre_tactic": "Execution",
        "mitre_technique_id": "T1059.004",
        "mitre_technique_name": "Unix Shell",
        "description": "Executes harmless base64 decoded command to test obfuscation detection.",
        "severity": "HIGH",
        "safe_payload_type": "BENIGN_COMMAND",
        "command_template": "echo 'aWQ=' | base64 -d | sh",
        "expected_detection_rule": "RULE_SUSPICIOUS_REVERSE_SHELL",
        "is_atomic": True
    }
]


class PurpleTeamEngine:
    def __init__(self, db: Session, organization_id: str):
        self.db = db
        self.organization_id = organization_id
        self.siem_engine = SIEMEngine()
        self.ensure_default_scenarios()

    def ensure_default_scenarios(self):
        """Seeds default atomic purple team scenarios if none exist."""
        existing_count = self.db.query(SimulationScenario).count()
        if existing_count == 0:
            for item in DEFAULT_SCENARIOS:
                scen = SimulationScenario(**item)
                self.db.add(scen)
            self.db.commit()

    def get_scenarios(self, tactic: Optional[str] = None) -> List[SimulationScenario]:
        query = self.db.query(SimulationScenario)
        if tactic:
            query = query.filter(SimulationScenario.mitre_tactic == tactic)
        return query.order_by(SimulationScenario.mitre_tactic, SimulationScenario.name).all()

    def execute_scenario(
        self,
        scenario_id: str,
        target_asset_id: Optional[str] = None,
        executed_by: str = "operator",
        parameters: Optional[Dict[str, Any]] = None
    ) -> SimulationExecution:
        """Executes a safe atomic scenario, correlates against SIEM rules, and records validation outcome."""
        scenario = self.db.query(SimulationScenario).filter(SimulationScenario.id == scenario_id).first()
        if not scenario:
            raise ValueError(f"Scenario '{scenario_id}' not found.")

        target_name = "Synthetic Endpoint"
        target_asset = None
        if target_asset_id:
            target_asset = self.db.query(Asset).filter(
                Asset.id == target_asset_id,
                Asset.organization_id == self.organization_id
            ).first()
            if target_asset:
                target_name = target_asset.name

        start_time = datetime.now(timezone.utc)
        exec_id = f"exec-{str(uuid.uuid4())[:8]}"

        execution = SimulationExecution(
            id=exec_id,
            organization_id=self.organization_id,
            scenario_id=scenario.id,
            target_asset_id=target_asset.id if target_asset else None,
            target_name=target_name,
            executed_by=executed_by,
            status=SimulationStatus.RUNNING,
            executed_at=start_time,
            completed_at=start_time,
            execution_log=f"Initiating purple-team atomic test: {scenario.name} against {target_name}...\n",
            telemetry_generated=json.dumps({"scenario_id": scenario.id, "technique": scenario.mitre_technique_id})
        )
        self.db.add(execution)
        self.db.flush()

        # Ingest controlled security events into the SIEM pipeline to validate detection
        generated_events = self._generate_controlled_telemetry(scenario, target_asset, target_name)
        
        # Check for matching SecurityAlert triggered after start_time
        # In SQLite/SQLAlchemy testing, alert timestamps might be identical or within milliseconds
        window_start = start_time - timedelta(seconds=2)
        matched_alert = None
        if scenario.expected_detection_rule:
            matched_alert = self.db.query(SecurityAlert).filter(
                SecurityAlert.organization_id == self.organization_id,
                SecurityAlert.created_at >= window_start,
                SecurityAlert.rule_id == scenario.expected_detection_rule
            ).order_by(SecurityAlert.created_at.desc()).first()

        end_time = datetime.now(timezone.utc)
        latency = round((end_time - start_time).total_seconds(), 3)

        if matched_alert:
            det_status = DetectionStatus.DETECTED
            verification = f"Detection validated successfully! Rule '{matched_alert.title}' triggered alert {matched_alert.id} ({latency}s latency)."
            rule_id = matched_alert.rule_id
            alert_id = matched_alert.id
        else:
            det_status = DetectionStatus.MISSED
            verification = f"Simulation completed without triggering expected rule '{scenario.expected_detection_rule or 'None'}'. Potential detection coverage gap."
            rule_id = None
            alert_id = None

        val_result = ValidationResult(
            id=f"val-{str(uuid.uuid4())[:8]}",
            execution_id=execution.id,
            detection_status=det_status,
            matched_alert_id=alert_id,
            matched_rule_id=rule_id,
            detection_latency_seconds=latency,
            verification_details=verification,
            created_at=end_time
        )
        self.db.add(val_result)

        execution.status = SimulationStatus.COMPLETED
        execution.completed_at = end_time
        execution.execution_log += f"Payload dispatch complete ({len(generated_events)} events ingested).\n"
        execution.execution_log += f"Outcome: {det_status} - {verification}\n"

        self.db.commit()
        self.db.refresh(execution)
        return execution

    def _generate_controlled_telemetry(
        self,
        scenario: SimulationScenario,
        target_asset: Optional[Asset],
        target_name: str
    ) -> List[SecurityEvent]:
        """Dispatches benign events designed to evaluate detection rules."""
        events: List[SecurityEvent] = []
        host = target_name
        aid = target_asset.id if target_asset else f"sim-{scenario.id[:6]}"

        if scenario.id == "scen-t1110-brute-force":
            # Ingest 6 failed SSH logon events with action="FAILURE"
            for i in range(6):
                evt_in = SecurityEventCreate(
                    category=EventCategory.AUTHENTICATION,
                    severity=EventSeverity.LOW,
                    action="FAILURE",
                    message=f"Failed SSH password attempt {i+1} for user root from 192.168.1.199",
                    asset_id=aid,
                    hostname=host,
                    source_ip="192.168.1.199",
                    destination_ip="10.10.20.15",
                    mitre_tactic="Credential Access",
                    mitre_technique_id="T1110",
                    mitre_technique_name="Brute Force",
                    raw_data={"attempt": i+1, "service": "sshd", "simulated": True}
                )
                events.append(self.siem_engine.ingest_event(self.db, evt_in, self.organization_id))

        elif scenario.id == "scen-t1548-sudo-abuse":
            evt_in = SecurityEventCreate(
                category=EventCategory.PROCESS_EXECUTION,
                severity=EventSeverity.HIGH,
                action="SUDO_COMMAND_EXECUTION",
                message="User operator executed sudo: sudo -u root /bin/bash (unauthorized privilege escalation)",
                asset_id=aid,
                hostname=host,
                source_ip="10.10.20.15",
                mitre_tactic="Privilege Escalation",
                mitre_technique_id="T1548.003",
                mitre_technique_name="Sudo and Sudo Caching",
                raw_data={"command": "sudo -u root /bin/bash", "user": "operator", "simulated": True}
            )
            events.append(self.siem_engine.ingest_event(self.db, evt_in, self.organization_id))

        elif scenario.id == "scen-t1003-shadow-dump":
            evt_in = SecurityEventCreate(
                category=EventCategory.FILE_INTEGRITY,
                severity=EventSeverity.CRITICAL,
                action="SENSITIVE_FILE_ACCESS",
                message="Unauthorized read access attempt on /etc/shadow",
                asset_id=aid,
                hostname=host,
                source_ip="10.10.20.15",
                mitre_tactic="Credential Access",
                mitre_technique_id="T1003.008",
                mitre_technique_name="/etc/passwd and /etc/shadow",
                raw_data={"filepath": "/etc/shadow", "mode": "r", "simulated": True}
            )
            events.append(self.siem_engine.ingest_event(self.db, evt_in, self.organization_id))

        elif scenario.id == "scen-t1046-port-scan":
            for port in [21, 22, 23, 25, 80, 110, 139, 443, 445, 1433, 3306, 8080]:
                evt_in = SecurityEventCreate(
                    category=EventCategory.NETWORK_CONNECTION,
                    severity=EventSeverity.LOW,
                    action="TCP_SYN_PROBE",
                    message=f"Rapid socket probes to port {port} (port scan detected)",
                    asset_id=aid,
                    hostname=host,
                    source_ip="192.168.1.199",
                    destination_ip="10.10.20.15",
                    mitre_tactic="Discovery",
                    mitre_technique_id="T1046",
                    mitre_technique_name="Network Service Discovery",
                    raw_data={"dest_port": port, "simulated": True}
                )
                events.append(self.siem_engine.ingest_event(self.db, evt_in, self.organization_id))

        elif scenario.id == "scen-t1059-shell-exec":
            evt_in = SecurityEventCreate(
                category=EventCategory.PROCESS_EXECUTION,
                severity=EventSeverity.HIGH,
                action="SUSPICIOUS_SHELL_COMMAND",
                message="Execution of suspicious reverse shell payload (/bin/bash -i)",
                asset_id=aid,
                hostname=host,
                source_ip="10.10.20.15",
                mitre_tactic="Execution",
                mitre_technique_id="T1059.004",
                mitre_technique_name="Unix Shell",
                raw_data={"command": "base64 -d | sh", "simulated": True}
            )
            events.append(self.siem_engine.ingest_event(self.db, evt_in, self.organization_id))

        else:
            # Benign baseline probe (e.g. system info discovery)
            evt_in = SecurityEventCreate(
                category=EventCategory.PROCESS_EXECUTION,
                severity=EventSeverity.INFORMATIONAL,
                action="BENIGN_SYSTEM_PROBE",
                message=f"Executed safe baseline query: {scenario.name}",
                asset_id=aid,
                hostname=host,
                mitre_tactic=scenario.mitre_tactic,
                mitre_technique_id=scenario.mitre_technique_id,
                mitre_technique_name=scenario.mitre_technique_name,
                raw_data={"command": scenario.command_template, "simulated": True}
            )
            events.append(self.siem_engine.ingest_event(self.db, evt_in, self.organization_id))

        return events

    def run_campaign(
        self,
        target_asset_id: Optional[str] = None,
        tactic_filter: Optional[str] = None,
        executed_by: str = "operator"
    ) -> RunCampaignResponse:
        """Runs a complete test suite across atomic scenarios to benchmark defensive posture."""
        scenarios = self.get_scenarios(tactic_filter)
        executions: List[SimulationExecutionResponse] = []
        detected_count = 0
        missed_count = 0

        campaign_id = f"camp-{str(uuid.uuid4())[:8]}"

        for scen in scenarios:
            exec_rec = self.execute_scenario(scen.id, target_asset_id, executed_by)
            if exec_rec.validation_result and exec_rec.validation_result.detection_status == DetectionStatus.DETECTED:
                detected_count += 1
            else:
                missed_count += 1

            val_res_dto = None
            if exec_rec.validation_result:
                val_res_dto = ValidationResultResponse(
                    id=exec_rec.validation_result.id,
                    execution_id=exec_rec.validation_result.execution_id,
                    detection_status=exec_rec.validation_result.detection_status,
                    matched_alert_id=exec_rec.validation_result.matched_alert_id,
                    matched_rule_id=exec_rec.validation_result.matched_rule_id,
                    detection_latency_seconds=exec_rec.validation_result.detection_latency_seconds,
                    verification_details=exec_rec.validation_result.verification_details,
                    created_at=exec_rec.validation_result.created_at
                )

            executions.append(SimulationExecutionResponse(
                id=exec_rec.id,
                organization_id=exec_rec.organization_id,
                scenario_id=exec_rec.scenario_id,
                scenario_name=scen.name,
                mitre_technique_id=scen.mitre_technique_id,
                mitre_tactic=scen.mitre_tactic,
                target_asset_id=exec_rec.target_asset_id,
                target_name=exec_rec.target_name,
                executed_by=exec_rec.executed_by,
                status=exec_rec.status,
                executed_at=exec_rec.executed_at,
                completed_at=exec_rec.completed_at,
                execution_log=exec_rec.execution_log,
                validation_result=val_res_dto
            ))

        total = detected_count + missed_count
        rate = round((detected_count / max(1, total)) * 100.0, 1)

        return RunCampaignResponse(
            campaign_id=campaign_id,
            total_scenarios_executed=total,
            detected_count=detected_count,
            missed_count=missed_count,
            efficacy_rate_pct=rate,
            executions=executions
        )

    def get_coverage_matrix(self) -> MitreCoverageResponse:
        """Calculates MITRE ATT&CK coverage and identifies defensive gaps."""
        all_scenarios = self.db.query(SimulationScenario).all()
        executions = self.db.query(SimulationExecution).filter(
            SimulationExecution.organization_id == self.organization_id
        ).all()

        exec_by_scenario: Dict[str, List[SimulationExecution]] = {}
        for ex in executions:
            exec_by_scenario.setdefault(ex.scenario_id, []).append(ex)

        coverage_items: List[MitreCoverageItem] = []
        covered_count = 0
        gap_count = 0

        for scen in all_scenarios:
            scen_execs = exec_by_scenario.get(scen.id, [])
            total_sim = len(scen_execs)
            detected = sum(1 for e in scen_execs if e.validation_result and e.validation_result.detection_status == DetectionStatus.DETECTED)

            if total_sim == 0:
                # If never tested yet, check if there's an expected rule
                if scen.expected_detection_rule:
                    status = "COVERED"
                    efficacy = 100.0
                    covered_count += 1
                else:
                    status = "GAP"
                    efficacy = 0.0
                    gap_count += 1
            else:
                efficacy = round((detected / total_sim) * 100.0, 1)
                if efficacy >= 80.0:
                    status = "COVERED"
                    covered_count += 1
                elif efficacy > 0.0:
                    status = "PARTIAL"
                    covered_count += 1
                else:
                    status = "GAP"
                    gap_count += 1

            coverage_items.append(MitreCoverageItem(
                tactic=scen.mitre_tactic,
                technique_id=scen.mitre_technique_id,
                technique_name=scen.mitre_technique_name,
                total_simulated=total_sim,
                detected_count=detected,
                coverage_status=status,
                detection_efficacy_pct=efficacy,
                rule_name=scen.expected_detection_rule
            ))

        total_tested = len(coverage_items)
        overall_cov = round((covered_count / max(1, total_tested)) * 100.0, 1)

        return MitreCoverageResponse(
            total_techniques_tested=total_tested,
            covered_techniques=covered_count,
            gap_techniques=gap_count,
            overall_coverage_pct=overall_cov,
            coverage_items=coverage_items
        )

    def get_kpis(self) -> PurpleTeamKPIs:
        """Calculates defensive validation KPIs."""
        executions = self.db.query(SimulationExecution).filter(
            SimulationExecution.organization_id == self.organization_id
        ).all()

        total = len(executions)
        detected = 0
        missed = 0
        latencies = []
        by_tactic: Dict[str, Dict[str, int]] = {}

        for ex in executions:
            tactic = ex.scenario.mitre_tactic if ex.scenario else "Other"
            by_tactic.setdefault(tactic, {"detected": 0, "total": 0})
            by_tactic[tactic]["total"] += 1

            if ex.validation_result and ex.validation_result.detection_status == DetectionStatus.DETECTED:
                detected += 1
                by_tactic[tactic]["detected"] += 1
                if ex.validation_result.detection_latency_seconds > 0:
                    latencies.append(ex.validation_result.detection_latency_seconds)
            else:
                missed += 1

        overall_rate = round((detected / max(1, total)) * 100.0, 1) if total > 0 else 0.0
        mttd = round(sum(latencies) / max(1, len(latencies)), 2) if latencies else 0.0

        by_tactic_efficacy = {}
        for tac, counts in by_tactic.items():
            by_tactic_efficacy[tac] = round((counts["detected"] / max(1, counts["total"])) * 100.0, 1)

        return PurpleTeamKPIs(
            total_simulations=total,
            total_detected=detected,
            total_missed=missed,
            overall_efficacy_rate=overall_rate,
            mean_time_to_detect_seconds=mttd,
            by_tactic_efficacy=by_tactic_efficacy
        )
