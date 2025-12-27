"""
Unit test for metrics endpoint.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_metrics_endpoint(client, monkeypatch):
    from app.api.v1 import metrics
    from app.schemas.common import MetricsResponse

    # Dependency override for get_db
    def fake_get_db():
        class DummyDB:
            def query(self, *args, **kwargs):
                class DummyQuery:
                    def count(self):
                        return 42
                    def filter(self, *a, **k):
                        return self
                return DummyQuery()
        yield DummyDB()

    app.dependency_overrides[metrics.get_db] = fake_get_db

    # Patch enums to avoid attribute errors
    class DummyStatusType:
        enums = ["PAID", "SHIPPED"]
    class DummyOrderTable:
        class columns:
            class status:
                type = DummyStatusType()

    class DummyOrder:
        __table__ = DummyOrderTable()
        status = "PAID"
    metrics.Order = DummyOrder

    class DummyReturnStatusType:
        enums = ["REQUESTED"]
    class DummyReturnTable:
        class columns:
            class status:
                type = DummyReturnStatusType()
    class DummyReturnRequest:
        __table__ = DummyReturnTable()
        status = "REQUESTED"
    metrics.ReturnRequest = DummyReturnRequest

    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "orders" in data
    assert "returns" in data
    assert "performance" in data
    assert isinstance(data["orders"], dict)
    assert isinstance(data["returns"], dict)
    assert isinstance(data["performance"], dict)
