"""
Tests for Unified SOC Hardening & Integrations:
- Token revocation on logout
- RBAC enforcement on Sites, Vulnerabilities, and Purple-Team
- Agent enrollment key gate & telemetry-to-SIEM forwarding
- Threat Intel IOC matching & Deception trap triggers
- Syslog & Suricata NDR log ingestion
- Version-grounded CVE matching (preventing port-only false positives)
"""
import json
from app.core.config import settings
from app.models.asset import Asset, AssetType, AssetCriticality, AssetStatus
from app.models.user import User
from app.vulnerability.engine import VulnerabilityEngine


def test_logout_revokes_jwt_token(client):
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "CyberLab@Admin2026!"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 200
    # Logged-out token must now be rejected
    res_after = client.get("/api/v1/auth/me", headers=headers)
    assert res_after.status_code == 401


def test_auditor_blocked_from_mutating_sites_vulns_and_purple_team(client, auditor_token):
    headers = {"Authorization": f"Bearer {auditor_token}"}
    assert client.post("/api/v1/sites", json={"name": "Rogue Site"}, headers=headers).status_code == 403
    assert client.post("/api/v1/vulnerabilities/scan", json={}, headers=headers).status_code == 403
    assert client.post("/api/v1/purple-team/execute", json={"scenario_id": "scen-t1082-sysinfo"}, headers=headers).status_code == 403


def test_agent_enrollment_key_enforcement(client, monkeypatch):
    monkeypatch.setattr(settings, "AGENT_ENROLLMENT_KEY", "company-secret-enroll-2026")
    payload = {"hostname": "corp-laptop-01", "ip_address": "10.20.1.55", "agent_version": "1.0.0"}

    # Missing key -> rejected
    assert client.post("/api/v1/agents/register", json=payload).status_code == 401
    # Wrong key -> rejected
    assert client.post(
        "/api/v1/agents/register",
        json=payload,
        headers={"X-CyberLab-Enrollment-Key": "wrong-key"},
    ).status_code == 401
    # Valid key -> accepted
    ok_res = client.post(
        "/api/v1/agents/register",
        json=payload,
        headers={"X-CyberLab-Enrollment-Key": "company-secret-enroll-2026"},
    )
    assert ok_res.status_code == 201


def test_agent_telemetry_triggers_siem_fim_and_ioc_alerts(client, admin_token):
    reg = client.post(
        "/api/v1/agents/register",
        json={"hostname": "finance-ws-01", "ip_address": "10.20.2.15", "agent_version": "1.0.0"}
    )
    assert reg.status_code == 201
    agent_id = reg.json()["agent_id"]
    agent_token = reg.json()["agent_token"]

    # Ensure Threat Intel defaults are seeded
    admin_hdr = {"Authorization": f"Bearer {admin_token}"}
    iocs = client.get("/api/v1/threat-intel/iocs", headers=admin_hdr)
    assert iocs.status_code == 200
    assert len(iocs.json()) >= 3

    # Agent sends FIM modification on /etc/shadow + active socket to malicious IOC 198.51.100.50
    tel_res = client.post(
        "/api/v1/agents/telemetry",
        headers={"Authorization": f"Bearer {agent_token}", "X-CyberLab-Agent-ID": agent_id},
        json={
            "cpu_pct": 12.5,
            "memory_pct": 40.0,
            "disk_pct": 25.0,
            "network_connections": [
                {"protocol": "TCP", "local_port": 51234, "local": "10.20.2.15:51234", "remote": "198.51.100.50:443", "state": "ESTABLISHED"}
            ],
            "fim_alerts": [
                {"action": "MODIFIED", "path": "/etc/shadow", "message": "SHA-256 hash changed on /etc/shadow", "severity": "CRITICAL"}
            ],
            "auth_events": [],
            "installed_packages": [{"package": "openssl", "version": "3.0.13-1"}],
        }
    )
    assert tel_res.status_code == 200

    alerts = client.get("/api/v1/siem/alerts", headers=admin_hdr).json()
    rule_ids = {a["rule_id"] for a in alerts}
    assert "RULE_CREDENTIAL_DUMPING_SHADOW" in rule_ids
    assert "RULE_THREAT_INTEL_IOC_MATCH" in rule_ids


def test_syslog_ndr_and_deception_trap_detection(client, admin_token):
    hdr = {"Authorization": f"Bearer {admin_token}"}

    # 1. Ingest Suricata EVE alert via NDR API
    ndr_res = client.post(
        "/api/v1/siem/ingest/ndr",
        headers=hdr,
        json={
            "engine": "suricata",
            "events": [
                {
                    "event_type": "alert",
                    "src_ip": "198.51.100.50",
                    "dest_ip": "10.0.0.10",
                    "dest_port": 445,
                    "alert": {"signature": "ET EXPLOIT EternalBlue SMB Probe", "severity": 1},
                }
            ],
        },
    )
    assert ndr_res.status_code == 201

    # 2. Ingest OPNsense syslog line
    sys_res = client.post(
        "/api/v1/siem/ingest/syslog",
        headers=hdr,
        json={
            "source_name": "opnsense-gw",
            "lines": [
                "filterlog: 42,,,1000000103,em0,match,block,in,4,0x0,,64,1234,0,none,6,tcp,60,203.0.113.66,10.0.0.10,44444,22,0,S"
            ],
        },
    )
    assert sys_res.status_code == 201

    # 3. Trigger Deception Trap
    traps = client.get("/api/v1/threat-intel/traps", headers=hdr).json()
    assert len(traps) >= 1
    trig = client.post(f"/api/v1/threat-intel/traps/{traps[0]['id']}/trigger", headers=hdr)
    assert trig.status_code == 200
    assert trig.json()["triggered_count"] >= 1

    alerts = client.get("/api/v1/siem/alerts", headers=hdr).json()
    rule_ids = {a["rule_id"] for a in alerts}
    assert "RULE_NDR_SURICATA_ALERT" in rule_ids
    assert "RULE_DECEPTION_TRAP_TRIGGERED" in rule_ids


def test_versioned_package_cve_matching_prevents_false_positives(db):
    admin_user = db.query(User).filter_by(username="admin").first()
    engine = VulnerabilityEngine(db, admin_user.organization_id)

    # Modern hardened server on ports 22 and 443 with patched OpenSSL 3.0.13
    safe_asset = Asset(
        id="asset-hardened-modern",
        organization_id=admin_user.organization_id,
        name="Hardened Modern Debian Server",
        asset_type=AssetType.AGENT_HOST,
        criticality=AssetCriticality.MEDIUM,
        risk_score=10,
        status=AssetStatus.ACTIVE,
        services_json=json.dumps([
            {"port": 22, "service": "sshd"},
            {"port": 443, "service": "nginx"},
            {"package": "openssl", "version": "3.0.13-0ubuntu3"},
            {"package": "openssh-server", "version": "1:9.6p1-3"},
        ]),
        security_tags_json=json.dumps([]),
    )
    db.add(safe_asset)
    db.commit()

    findings = engine.scan_asset(safe_asset)
    assert len(findings) == 0
