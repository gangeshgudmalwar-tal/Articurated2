"""
State Machine implementation for order and return state transitions.

Uses data-driven dictionaries for validation instead of if/else chains.
"""
from enum import Enum
from typing import Dict, List


class OrderStatus(str, Enum):
    """Order states from PRD."""
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"
    PROCESSING_IN_WAREHOUSE = "PROCESSING_IN_WAREHOUSE"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class ReturnStatus(str, Enum):
    """Return request states from PRD."""
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    IN_TRANSIT = "IN_TRANSIT"
    RECEIVED = "RECEIVED"
    COMPLETED = "COMPLETED"


# Data-driven state transition rules
ORDER_TRANSITIONS: Dict[OrderStatus, List[OrderStatus]] = {
    OrderStatus.PENDING_PAYMENT: [OrderStatus.PAID, OrderStatus.CANCELLED],
    OrderStatus.PAID: [OrderStatus.PROCESSING_IN_WAREHOUSE, OrderStatus.CANCELLED],
    OrderStatus.PROCESSING_IN_WAREHOUSE: [OrderStatus.SHIPPED],
    OrderStatus.SHIPPED: [OrderStatus.DELIVERED],
    OrderStatus.DELIVERED: [],  # Terminal state
    OrderStatus.CANCELLED: [],  # Terminal state
}

RETURN_TRANSITIONS: Dict[ReturnStatus, List[ReturnStatus]] = {
    ReturnStatus.REQUESTED: [ReturnStatus.APPROVED, ReturnStatus.REJECTED],
    ReturnStatus.APPROVED: [ReturnStatus.IN_TRANSIT],
    ReturnStatus.REJECTED: [],  # Terminal state
    ReturnStatus.IN_TRANSIT: [ReturnStatus.RECEIVED],
    ReturnStatus.RECEIVED: [ReturnStatus.COMPLETED],
    ReturnStatus.COMPLETED: [],  # Terminal state
}


class StateMachine:
    """Validates state transitions for orders and returns."""

    @staticmethod
    def can_transition(
        current_state: OrderStatus | ReturnStatus,
        new_state: OrderStatus | ReturnStatus,
        is_order: bool = True,
    ) -> bool:
        """
        Check if transition is allowed.
        """
        if is_order:
            allowed = ORDER_TRANSITIONS.get(current_state, [])
        else:
            allowed = RETURN_TRANSITIONS.get(current_state, [])
        return new_state in allowed

    @staticmethod
    def get_allowed_transitions(
        current_state: OrderStatus | ReturnStatus,
        is_order: bool = True,
    ) -> List[OrderStatus | ReturnStatus]:
        """
        Return allowed transitions for the current state.
        """
        if is_order:
            return ORDER_TRANSITIONS.get(current_state, [])
        else:
            return RETURN_TRANSITIONS.get(current_state, [])

    @staticmethod
    def validate_transition(
        current_state: OrderStatus | ReturnStatus,
        new_state: OrderStatus | ReturnStatus,
        is_order: bool = True,
    ) -> None:
        """
        Raise InvalidStateTransitionError if not allowed, else return None.
        """
        if not StateMachine.can_transition(current_state, new_state, is_order=is_order):
            from app.utils.exceptions import InvalidStateTransitionError
            allowed = StateMachine.get_allowed_transitions(current_state, is_order=is_order)
            raise InvalidStateTransitionError(
                current_state=current_state,
                requested_state=new_state,
                allowed_transitions=allowed
            )
        # else: valid, do nothing
            return  # Remove the incomplete docstring and code

    @staticmethod
    def validate_transition(
        current_state: OrderStatus | ReturnStatus,
        new_state: OrderStatus | ReturnStatus,
        is_order: bool = True,
    ) -> None:
        """
        Validate transition or raise exception.
        
        Args:
            current_state: Current state
            new_state: Requested new state
            is_order: True for orders, False for returns
            
        Raises:
            ValueError: If transition is not allowed
        """
        from app.utils.exceptions import InvalidStateTransitionError
        
        if not StateMachine.can_transition(current_state, new_state, is_order):
            allowed = StateMachine.get_allowed_transitions(current_state, is_order)
            raise InvalidStateTransitionError(
                current_state=str(current_state),
                requested_state=str(new_state),
                allowed_transitions=[str(s) for s in allowed],
            )
