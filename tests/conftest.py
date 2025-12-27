"""
Test configuration and fixtures.
"""
import os

# Ensure tests run in isolated settings with in-memory services
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")
os.environ.setdefault("CELERY_BROKER_URL", "memory://")
os.environ.setdefault("CELERY_RESULT_BACKEND", "cache+memory://")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.database import Base, get_db
from app.main import app
from app.models import order as _order_model  # ensure models are registered
from app.models import return_request as _return_model
from app.models import state_history as _state_history_model

# Test database URL (use in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override and API key header."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    class APIKeyTestClient(TestClient):
        def request(self, method, url, **kwargs):
            headers = kwargs.pop("headers", {}) or {}
            headers["X-API-Key"] = "dev-api-key"
            kwargs["headers"] = headers
            return super().request(method, url, **kwargs)

    with APIKeyTestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_order_data():
    """Sample order creation data."""
    return {
        "customer_id": "CUST123",
        "shipping_address": {
            "street": "123 Main St",
            "city": "New York",
            "state": "NY",
            "postal_code": "10001",
            "country": "USA",
        },
        "billing_address": {
            "street": "123 Main St",
            "city": "New York",
            "state": "NY",
            "postal_code": "10001",
            "country": "USA",
        },
        "payment_method": "credit_card",
        "line_items": [
            {
                "product_id": "PROD001",
                "product_name": "Test Product",
                "quantity": 2,
                "unit_price": "25.00",
            }
        ],
    }


@pytest.fixture
def sample_return_data():
    """Sample return creation data."""
    return {
        "order_id": 1,
        "reason": "Product damaged",
        "requested_by": "CUST123",
        "items": [{"line_item_id": 1, "quantity": 1}],
        "refund_amount": "25.00",
    }
