"""
Tests for Authentication & Profile Endpoints
"""


def test_login_success(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "CyberLab@Admin2026!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "super_admin"


def test_login_invalid_password(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "WrongPassword123!"}
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_login_nonexistent_user(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "nonexistent_user", "password": "RandomPassword123!"}
    )
    assert response.status_code == 401


def test_auth_me_authenticated(client, admin_token):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert data["role"] == "super_admin"


def test_auth_me_unauthenticated(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_auth_me_invalid_token(client):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_malformed_token"}
    )
    assert response.status_code == 401
