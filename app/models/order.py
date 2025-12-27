"""
Order and OrderLineItem SQLAlchemy models.
"""
from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    ForeignKey,
    Enum,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, JSONType
from app.services.state_machine import OrderStatus


class Order(Base, TimestampMixin):
    """Order model representing a customer order."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(100), nullable=False, index=True)
    status = Column(
        Enum(OrderStatus, name="order_status_enum"),
        default=OrderStatus.PENDING_PAYMENT,
        nullable=False,
        index=True,
    )
    
    # Address stored as JSON/JSONB for flexibility (cross-dialect via JSONType)
    shipping_address = Column(JSONType, nullable=False)
    billing_address = Column(JSONType, nullable=False)
    
    # Pricing
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax = Column(Numeric(10, 2), nullable=False)
    shipping_cost = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    
    # Payment
    payment_method = Column(String(50), nullable=False)
    payment_transaction_id = Column(String(200), nullable=True)
    
    # Shipping
    tracking_number = Column(String(200), nullable=True, index=True)
    carrier = Column(String(100), nullable=True)
    
    # Additional metadata (avoid reserved attribute name 'metadata' on declarative Base)
    extra_metadata = Column("metadata", JSONType, nullable=True)

    # Relationships
    line_items = relationship(
        "OrderLineItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )
    state_history = relationship(
        "StateHistory",
        back_populates="order",
        cascade="all, delete-orphan",
        foreign_keys="StateHistory.order_id",
    )
    return_requests = relationship(
        "ReturnRequest",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="check_subtotal_positive"),
        CheckConstraint("tax >= 0", name="check_tax_positive"),
        CheckConstraint("shipping_cost >= 0", name="check_shipping_cost_positive"),
        CheckConstraint("total >= 0", name="check_total_positive"),
        Index("idx_order_customer_status", "customer_id", "status"),
        Index("idx_order_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, customer_id={self.customer_id}, status={self.status})>"


class OrderLineItem(Base, TimestampMixin):
    """Line item within an order."""

    __tablename__ = "order_line_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    
    product_id = Column(String(100), nullable=False)
    product_name = Column(String(500), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    
    # Product metadata
    extra_metadata = Column("metadata", JSONType, nullable=True)

    # Relationships
    order = relationship("Order", back_populates="line_items")

    # Constraints
    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="check_unit_price_positive"),
        CheckConstraint("subtotal >= 0", name="check_item_subtotal_positive"),
        Index("idx_line_item_product", "product_id"),
    )

    def __repr__(self) -> str:
        return f"<OrderLineItem(id={self.id}, product_id={self.product_id}, quantity={self.quantity})>"
