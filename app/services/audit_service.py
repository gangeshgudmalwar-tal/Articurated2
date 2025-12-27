"""
Audit service for recording state transitions.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.state_history import StateHistory


class AuditService:
    """Service for audit trail operations."""

    def __init__(self, db: Session):
        self.db = db

    def record_state_change(
        self,
        new_state: str,
        actor: str,
        trigger: str = "API",
        order_id: Optional[int] = None,
        return_request_id: Optional[int] = None,
        previous_state: Optional[str] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
    ) -> StateHistory:
        """
        Record an immutable state transition in the audit trail.
        
        Args:
            order_id: Order ID (for order transitions)
            return_request_id: Return ID (for return transitions)
            previous_state: Previous state
            new_state: New state
            actor: User ID or SYSTEM
            trigger: Source of transition (API, WEBHOOK, BACKGROUND_JOB)
            ip_address: Client IP address
            metadata: Additional context
            notes: Human-readable notes
            
        Returns:
            Created state history record
        """
        def _state_value(state: Optional[str]) -> Optional[str]:
            if isinstance(state, Enum):
                return state.value
            return str(state) if state is not None else None

        history = StateHistory(
            order_id=order_id,
            return_request_id=return_request_id,
            previous_state=_state_value(previous_state),
            new_state=_state_value(new_state),
            actor=actor,
            trigger=trigger,
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            metadata=metadata,
            notes=notes,
        )
        
        self.db.add(history)
        # Note: caller should commit
        
        return history
