"""
StateHistory SQLAlchemy model for audit trail.
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import JSONType


class StateHistory(Base):
    """
    Immutable audit trail for state transitions.
    
    Records every state change for orders and returns.
    """

    __tablename__ = "state_history"

    id = Column(Integer, primary_key=True, index=True)
    
    # Polymorphic relationship (either order_id or return_request_id)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=True, index=True)
    return_request_id = Column(Integer, ForeignKey("return_requests.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # State transition details
    previous_state = Column(String(100), nullable=True)
    new_state = Column(String(100), nullable=False, index=True)
    
    # Actor and trigger
    actor = Column(String(100), nullable=False)  # User ID or "SYSTEM"
    trigger = Column(String(100), nullable=False)  # "API", "WEBHOOK", "BACKGROUND_JOB"
    
    # Audit information
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    
    # Additional context (avoid reserved name on declarative Base)
    extra_metadata = Column("metadata", JSONType, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    order = relationship("Order", back_populates="state_history", foreign_keys=[order_id])
    return_request = relationship("ReturnRequest", back_populates="state_history", foreign_keys=[return_request_id])

    # Constraints
    __table_args__ = (
        Index("idx_state_history_order_timestamp", "order_id", "timestamp"),
        Index("idx_state_history_return_timestamp", "return_request_id", "timestamp"),
        Index("idx_state_history_actor", "actor"),
    )

    def __repr__(self) -> str:
        entity_type = "order" if self.order_id else "return"
        entity_id = self.order_id or self.return_request_id
        return f"<StateHistory({entity_type}={entity_id}, {self.previous_state} → {self.new_state})>"
