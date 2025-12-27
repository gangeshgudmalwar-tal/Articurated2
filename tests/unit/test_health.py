"""
Unit test for health check endpoint.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_health_check(client, monkeypatch):
    # Patch DB and Redis to always return healthy
    monkeypatch.setattr("app.api.v1.health.health_check", lambda db=None: {
        "status": "healthy",
        "version": "1.0.0",
        "database": "healthy",
        "redis": "healthy"
    })

    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "database" in data
    assert "redis" in data
    assert data["version"] == "1.0.0"
