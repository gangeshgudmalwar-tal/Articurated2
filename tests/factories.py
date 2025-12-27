"""
Factory Boy factories for test data generation.
"""
import factory
from factory.alchemy import SQLAlchemyModelFactory
from decimal import Decimal
from app.models.order import Order, OrderLineItem
from app.models.return_request import ReturnRequest
from app.models.state_history import StateHistory
from app.services.state_machine import OrderStatus, ReturnStatus


class OrderFactory(SQLAlchemyModelFactory):
    """Factory for Order model."""

    class Meta:
        model = Order
        sqlalchemy_session_persistence = "commit"

    id = factory.Sequence(lambda n: n)
    customer_id = factory.Sequence(lambda n: f"CUST{n:03d}")
    status = OrderStatus.PENDING_PAYMENT
    shipping_address = {
        "street": "123 Test St",
        "city": "Test City",
        "state": "TS",
        "postal_code": "12345",
        "country": "USA",
    }
    billing_address = {
        "street": "123 Test St",
        "city": "Test City",
        "state": "TS",
        "postal_code": "12345",
        "country": "USA",
    }
    payment_method = "credit_card"
    subtotal = Decimal("100.00")
    tax = Decimal("10.00")
    shipping_cost = Decimal("10.00")
    total = Decimal("120.00")


class OrderLineItemFactory(SQLAlchemyModelFactory):
    """Factory for OrderLineItem model."""

    class Meta:
        model = OrderLineItem
        sqlalchemy_session_persistence = "commit"

    id = factory.Sequence(lambda n: n)
    order = factory.SubFactory(OrderFactory)
    product_id = factory.Sequence(lambda n: f"PROD{n:03d}")
    product_name = factory.Sequence(lambda n: f"Test Product {n}")
    quantity = 1
    unit_price = Decimal("50.00")
    subtotal = Decimal("50.00")


class ReturnRequestFactory(SQLAlchemyModelFactory):
    """Factory for ReturnRequest model."""

    class Meta:
        model = ReturnRequest
        sqlalchemy_session_persistence = "commit"

    id = factory.Sequence(lambda n: n)
    order = factory.SubFactory(OrderFactory)
    status = ReturnStatus.REQUESTED
    reason = "Test return reason"
    requested_by = factory.Sequence(lambda n: f"CUST{n:03d}")
    items = [{"line_item_id": 1, "quantity": 1}]
    refund_amount = Decimal("50.00")


class StateHistoryFactory(SQLAlchemyModelFactory):
    """Factory for StateHistory model."""

    class Meta:
        model = StateHistory
        sqlalchemy_session_persistence = "commit"

    id = factory.Sequence(lambda n: n)
    order = factory.SubFactory(OrderFactory)
    previous_state = None
    new_state = str(OrderStatus.PENDING_PAYMENT)
    actor = "CUST001"
    trigger = "API"
