"""
ReturnRequest SQLAlchemy model.
"""
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Numeric,
    ForeignKey,
    Enum,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, JSONType
from app.services.state_machine import ReturnStatus


class ReturnRequest(Base, TimestampMixin):
    """Return request model."""

    __tablename__ = "return_requests"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    
    status = Column(
        Enum(ReturnStatus, name="return_status_enum"),
        default=ReturnStatus.REQUESTED,
        nullable=False,
        index=True,
    )
    
    # Return details
    reason = Column(Text, nullable=False)
    requested_by = Column(String(100), nullable=False)  # customer_id
    
    # Items being returned (list of line item IDs and quantities)
    items = Column(JSONType, nullable=False)  # [{"line_item_id": 1, "quantity": 2}]
    
    # Refund information
    refund_amount = Column(Numeric(10, 2), nullable=False)
    refund_transaction_id = Column(String(200), nullable=True)
    
    # Approval/rejection
    approved_by = Column(String(100), nullable=True)  # admin user ID
    rejection_reason = Column(Text, nullable=True)
    
    # Shipping
    return_tracking_number = Column(String(200), nullable=True, index=True)
    return_carrier = Column(String(100), nullable=True)
    
    # Metadata (avoid reserved attribute name on declarative Base)
    extra_metadata = Column("metadata", JSONType, nullable=True)

    # Relationships
    order = relationship("Order", back_populates="return_requests")
    state_history = relationship(
        "StateHistory",
        back_populates="return_request",
        cascade="all, delete-orphan",
        foreign_keys="StateHistory.return_request_id",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("refund_amount >= 0", name="check_refund_amount_positive"),
        Index("idx_return_order_status", "order_id", "status"),
        Index("idx_return_requested_by", "requested_by"),
        Index("idx_return_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ReturnRequest(id={self.id}, order_id={self.order_id}, status={self.status})>"
