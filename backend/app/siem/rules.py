"""
SIEM Detection Rules & MITRE ATT&CK Mapping (Phase 6)
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from app.models.siem import SecurityEvent, EventCategory, EventSeverity


class DetectionRuleDef:
    def __init__(
        self,
        rule_id: str,
        title: str,
        description: str,
        severity: str,
        mitre_tactic: str,
        mitre_technique_id: str,
        mitre_technique_name: str,
    ):
        self.rule_id = rule_id
        self.title = title
        self.description = description
        self.severity = severity
        self.mitre_tactic = mitre_tactic
        self.mitre_technique_id = mitre_technique_id
        self.mitre_technique_name = mitre_technique_name

    def evaluate(self, event: SecurityEvent, recent_events: List[SecurityEvent]) -> bool:
        raise NotImplementedError


class BruteForceRule(DetectionRuleDef):
    def __init__(self):
        super().__init__(
            rule_id="RULE_AUTH_BRUTE_FORCE",
            title="Authentication Brute Force Attack Detected",
            description="Multiple consecutive failed login attempts detected against a host within a 5-minute window.",
            severity=EventSeverity.HIGH,
            mitre_tactic="Credential Access",
            mitre_technique_id="T1110",
            mitre_technique_name="Brute Force",
        )

    def evaluate(self, event: SecurityEvent, recent_events: List[SecurityEvent]) -> bool:
        if event.category != EventCategory.AUTHENTICATION or event.action != "FAILURE":
            return False

        # Count failed logins in recent events for the same host or source IP
        matches = 1
        for prev in recent_events:
            if prev.id == event.id:
                continue
            if prev.category == EventCategory.AUTHENTICATION and prev.action == "FAILURE":
                if (event.hostname and prev.hostname == event.hostname) or (event.source_ip and prev.source_ip == event.source_ip):
                    matches += 1

        return matches >= 3


class SudoPrivilegeEscalationRule(DetectionRuleDef):
    def __init__(self):
        super().__init__(
            rule_id="RULE_PRIVILEGE_ESCALATION_SUDO",
            title="Suspicious Sudo / Root Privilege Escalation Attempt",
            description="Unauthorized sudo elevation or root abuse detected via system authentication logs.",
            severity=EventSeverity.HIGH,
            mitre_tactic="Privilege Escalation",
            mitre_technique_id="T1548.003",
            mitre_technique_name="Sudo and Sudo Caching",
        )

    def evaluate(self, event: SecurityEvent, recent_events: List[SecurityEvent]) -> bool:
        msg = event.message.lower()
        if "sudo" in msg and ("not in sudoers" in msg or "incorrect password" in msg or "elevation failed" in msg or "privilege escalation" in msg):
            return True
        if "su: auth failure" in msg or "root privilege abuse" in msg:
            return True
        return False


class CredentialDumpingRule(DetectionRuleDef):
    def __init__(self):
        super().__init__(
            rule_id="RULE_CREDENTIAL_DUMPING_SHADOW",
            title="Credential Store Tampering / Shadow File Access",
            description="Critical system authentication files (/etc/shadow, /etc/passwd) modified or accessed unexpectedly.",
            severity=EventSeverity.CRITICAL,
            mitre_tactic="Credential Access",
            mitre_technique_id="T1003.008",
            mitre_technique_name="/etc/passwd and /etc/shadow",
        )

    def evaluate(self, event: SecurityEvent, recent_events: List[SecurityEvent]) -> bool:
        if event.category == EventCategory.FILE_INTEGRITY:
            msg = event.message.lower()
            if "/etc/shadow" in msg or "/etc/passwd" in msg or "/etc/sudoers" in msg:
                return True
        return False


class ReverseShellRule(DetectionRuleDef):
    def __init__(self):
        super().__init__(
            rule_id="RULE_SUSPICIOUS_REVERSE_SHELL",
            title="Suspicious Reverse Interactive Shell Spawned",
            description="Execution of interactive shell redirecting standard input/output over a network socket.",
            severity=EventSeverity.CRITICAL,
            mitre_tactic="Execution",
            mitre_technique_id="T1059.004",
            mitre_technique_name="Unix Shell",
        )

    def evaluate(self, event: SecurityEvent, recent_events: List[SecurityEvent]) -> bool:
        msg = event.message.lower()
        indicators = ["/bin/bash -i", "/bin/sh -i", "nc -e", "nc.traditional -e", "pty.spawn", "reverse shell", "socket.connect"]
        return any(ind in msg for ind in indicators)


class ReconnaissanceRule(DetectionRuleDef):
    def __init__(self):
        super().__init__(
            rule_id="RULE_PORT_SCAN_RECON",
            title="Network Port Scan / Reconnaissance Activity",
            description="Rapid connection probes across multiple ports or endpoints indicative of port scanning tools.",
            severity=EventSeverity.MEDIUM,
            mitre_tactic="Discovery",
            mitre_technique_id="T1046",
            mitre_technique_name="Network Service Discovery",
        )

    def evaluate(self, event: SecurityEvent, recent_events: List[SecurityEvent]) -> bool:
        msg = event.message.lower()
        if "port scan" in msg or "nmap syn scan" in msg or "rapid socket probes" in msg:
            return True
        return False


class SuricataIDSRule(DetectionRuleDef):
    def __init__(self):
        super().__init__(
            rule_id="RULE_NDR_SURICATA_ALERT",
            title="NDR / Network IDS Signature Alert",
            description="Network intrusion detection signature triggered via Suricata EVE or firewall NDR stream.",
            severity=EventSeverity.HIGH,
            mitre_tactic="Command and Control",
            mitre_technique_id="T1071",
            mitre_technique_name="Application Layer Protocol",
        )

    def evaluate(self, event: SecurityEvent, recent_events: List[SecurityEvent]) -> bool:
        if event.category == EventCategory.NETWORK_CONNECTION and event.action == "NDR_ALERT":
            return True
        return False


class ThreatIntelMatchRule(DetectionRuleDef):
    def __init__(self):
        super().__init__(
            rule_id="RULE_THREAT_INTEL_IOC_MATCH",
            title="Threat Intelligence IOC Match Detected",
            description="Traffic, socket, or log matched an active known-malicious Threat Intel IOC.",
            severity=EventSeverity.CRITICAL,
            mitre_tactic="Command and Control",
            mitre_technique_id="T1071",
            mitre_technique_name="Application Layer Protocol",
        )

    def evaluate(self, event: SecurityEvent, recent_events: List[SecurityEvent]) -> bool:
        raw = (event.raw_data_json or "").lower()
        return "threat_intel_ioc_match" in raw or "ioc_match" in event.message.lower()


class HoneypotDeceptionRule(DetectionRuleDef):
    def __init__(self):
        super().__init__(
            rule_id="RULE_DECEPTION_TRAP_TRIGGERED",
            title="Deception Honeypot / Canary Trap Triggered",
            description="Zero-false-positive detection: adversary touched a decoy credential, port, or canary file.",
            severity=EventSeverity.CRITICAL,
            mitre_tactic="Discovery",
            mitre_technique_id="T1083",
            mitre_technique_name="File and Directory Discovery",
        )

    def evaluate(self, event: SecurityEvent, recent_events: List[SecurityEvent]) -> bool:
        return event.action == "DECEPTION_TRAP_TRIGGERED" or "deception_trap_triggered" in event.message.lower()


ALL_RULES: List[DetectionRuleDef] = [
    BruteForceRule(),
    SudoPrivilegeEscalationRule(),
    CredentialDumpingRule(),
    ReverseShellRule(),
    ReconnaissanceRule(),
    SuricataIDSRule(),
    ThreatIntelMatchRule(),
    HoneypotDeceptionRule(),
]
