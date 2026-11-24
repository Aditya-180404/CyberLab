"""
Tests for Role-Based Access Control (RBAC)
"""


def test_admin_can_list_users(client, admin_token):
    response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 4  # admin, analyst, engineer, auditor
    usernames = [u["username"] for u in users]
    assert "admin" in usernames
    assert "analyst" in usernames


def test_admin_can_create_user(client, admin_token):
    new_user_payload = {
        "username": "new_sec_analyst",
        "email": "sec_analyst@cyberlab.local",
        "password": "SecurePassword123!",
        "role": "soc_analyst",
        "is_active": True
    }
    response = client.post(
        "/api/v1/users",
        json=new_user_payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "new_sec_analyst"
    assert data["role"] == "soc_analyst"


def test_analyst_cannot_create_user(client, analyst_token):
    new_user_payload = {
        "username": "unauthorized_user",
        "email": "unauth@cyberlab.local",
        "password": "SecurePassword123!",
        "role": "soc_analyst",
        "is_active": True
    }
    response = client.post(
        "/api/v1/users",
        json=new_user_payload,
        headers={"Authorization": f"Bearer {analyst_token}"}
    )
    # Must fail with 403 Forbidden
    assert response.status_code == 403
    assert "Operation not permitted" in response.json()["detail"]
