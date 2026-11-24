"""
Tests for Immutable Audit Log Records
"""


def test_audit_log_generation_on_login(client, admin_token):
    # Query audit logs as admin
    response = client.get(
        "/api/v1/audit",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) > 0
    actions = [log["action"] for log in logs]
    assert "USER_LOGIN_SUCCESS" in actions


def test_auditor_can_read_audit_logs(client, auditor_token):
    response = client.get(
        "/api/v1/audit",
        headers={"Authorization": f"Bearer {auditor_token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_analyst_cannot_read_audit_logs(client, analyst_token):
    # Standard analyst should not have direct access to raw compliance audit logs
    response = client.get(
        "/api/v1/audit",
        headers={"Authorization": f"Bearer {analyst_token}"}
    )
    assert response.status_code == 403
