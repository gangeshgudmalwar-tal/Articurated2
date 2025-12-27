"""
Unit tests for OrderService: state transitions, audit, and invoice trigger.
"""

import pytest
from unittest.mock import MagicMock
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers
from app.models.order import Order
from app.models.state_history import StateHistory
from app.services.order_service import OrderService
from app.services.state_machine import OrderStatus
from app.utils.exceptions import InvalidStateTransitionError
from tests.factories import OrderFactory
from app.database import Base


# Use a real in-memory SQLite DB for stateful tests
@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)

@pytest.fixture
def order_service(db_session):
    return OrderService(db_session)

@pytest.mark.parametrize("current,new,should_succeed", [
    (OrderStatus.PENDING_PAYMENT, OrderStatus.PAID, True),
    (OrderStatus.PAID, OrderStatus.PROCESSING_IN_WAREHOUSE, True),
    (OrderStatus.PROCESSING_IN_WAREHOUSE, OrderStatus.SHIPPED, True),
    (OrderStatus.SHIPPED, OrderStatus.DELIVERED, True),
    (OrderStatus.PAID, OrderStatus.CANCELLED, True),
    (OrderStatus.PENDING_PAYMENT, OrderStatus.CANCELLED, True),
    (OrderStatus.SHIPPED, OrderStatus.PAID, False),
    (OrderStatus.DELIVERED, OrderStatus.CANCELLED, False),
])
def test_order_state_transition(order_service, db_session, current, new, should_succeed):
    order = OrderFactory.build(status=current)
    db_session.add(order)
    db_session.commit()
    # Patch audit_service to avoid real DB writes for audit
    order_service.audit_service.record_state_change = MagicMock()

    if should_succeed:
        result = order_service.transition_state(
            order_id=order.id,
            new_state=new,
            actor_id="user-1",
            trigger="API_CALL",
            metadata={},
            ip_address="127.0.0.1"
        )
        assert result.status == new
        order_service.audit_service.record_state_change.assert_called_once()
    else:
        with pytest.raises(InvalidStateTransitionError):
            order_service.transition_state(
                order_id=order.id,
                new_state=new,
                actor_id="user-1",
                trigger="API_CALL",
                metadata={},
                ip_address="127.0.0.1"
            )
        order_service.audit_service.record_state_change.assert_not_called()

def test_invoice_trigger_on_shipped(order_service, db_session):
    order = OrderFactory.build(status=OrderStatus.PROCESSING_IN_WAREHOUSE)
    db_session.add(order)
    db_session.commit()
    order_service.audit_service.record_state_change = MagicMock()
    # Patch Celery task using unittest.mock.patch
    from unittest.mock import patch
    try:
        with patch("app.tasks.invoice_tasks.generate_invoice") as mock_generate_invoice:
            order_service.transition_state(
                order_id=order.id,
                new_state=OrderStatus.SHIPPED,
                actor_id="user-1",
                trigger="API_CALL",
                metadata={},
                ip_address="127.0.0.1"
            )
            mock_generate_invoice.delay.assert_called_once_with(str(order.id))
    except ModuleNotFoundError:
        pytest.skip("Celery not installed; skipping invoice trigger test.")
