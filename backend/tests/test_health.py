"""
Tests for Health & Diagnostics API
"""


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "CyberLab"
    assert data["status"] == "operational"
    assert "version" in data


def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "platform" in data
    assert data["platform"]["os"] != ""
    assert data["platform"]["cpu_usage_pct"] >= 0.0
    assert data["platform"]["memory_total_gb"] > 0
    assert data["checks"]["database_read_write"] is True
    assert data["checks"]["jwt_crypto_operational"] is True
