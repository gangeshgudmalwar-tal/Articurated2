"""
State machine unit tests.

Tests all valid and invalid state transitions.
"""
import pytest
from app.services.state_machine import StateMachine, OrderStatus, ReturnStatus
from app.utils.exceptions import InvalidStateTransitionError


class TestOrderStateMachine:
    """Test order state transitions."""

    # Valid transitions
    @pytest.mark.parametrize("current_state,new_state", [
        (OrderStatus.PENDING_PAYMENT, OrderStatus.PAID),
        (OrderStatus.PENDING_PAYMENT, OrderStatus.CANCELLED),
        (OrderStatus.PAID, OrderStatus.PROCESSING_IN_WAREHOUSE),
        (OrderStatus.PAID, OrderStatus.CANCELLED),
        (OrderStatus.PROCESSING_IN_WAREHOUSE, OrderStatus.SHIPPED),
        (OrderStatus.SHIPPED, OrderStatus.DELIVERED),
    ])
    def test_valid_order_transitions(self, current_state, new_state):
        """Test that valid order transitions are allowed."""
        assert StateMachine.can_transition(current_state, new_state, is_order=True)
        # Should not raise exception
        StateMachine.validate_transition(current_state, new_state, is_order=True)

    # Invalid transitions
    @pytest.mark.parametrize("current_state,new_state", [
        (OrderStatus.PENDING_PAYMENT, OrderStatus.PROCESSING_IN_WAREHOUSE),
        (OrderStatus.PENDING_PAYMENT, OrderStatus.SHIPPED),
        (OrderStatus.PENDING_PAYMENT, OrderStatus.DELIVERED),
        (OrderStatus.PAID, OrderStatus.PENDING_PAYMENT),
        (OrderStatus.PAID, OrderStatus.SHIPPED),
        (OrderStatus.PAID, OrderStatus.DELIVERED),
        (OrderStatus.PROCESSING_IN_WAREHOUSE, OrderStatus.PENDING_PAYMENT),
        (OrderStatus.PROCESSING_IN_WAREHOUSE, OrderStatus.PAID),
        (OrderStatus.PROCESSING_IN_WAREHOUSE, OrderStatus.DELIVERED),
        (OrderStatus.SHIPPED, OrderStatus.PENDING_PAYMENT),
        (OrderStatus.SHIPPED, OrderStatus.PAID),
        (OrderStatus.SHIPPED, OrderStatus.PROCESSING_IN_WAREHOUSE),
        (OrderStatus.SHIPPED, OrderStatus.CANCELLED),
        (OrderStatus.DELIVERED, OrderStatus.PENDING_PAYMENT),
        (OrderStatus.DELIVERED, OrderStatus.PAID),
        (OrderStatus.DELIVERED, OrderStatus.PROCESSING_IN_WAREHOUSE),
        (OrderStatus.DELIVERED, OrderStatus.SHIPPED),
        (OrderStatus.DELIVERED, OrderStatus.CANCELLED),
        (OrderStatus.CANCELLED, OrderStatus.PENDING_PAYMENT),
        (OrderStatus.CANCELLED, OrderStatus.PAID),
        (OrderStatus.CANCELLED, OrderStatus.PROCESSING_IN_WAREHOUSE),
        (OrderStatus.CANCELLED, OrderStatus.SHIPPED),
        (OrderStatus.CANCELLED, OrderStatus.DELIVERED),
    ])
    def test_invalid_order_transitions(self, current_state, new_state):
        """Test that invalid order transitions are rejected."""
        assert not StateMachine.can_transition(current_state, new_state, is_order=True)
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            StateMachine.validate_transition(current_state, new_state, is_order=True)
        
        # Verify error details
        error = exc_info.value
        assert error.code == "INVALID_STATE_TRANSITION"
        assert str(current_state) in error.message
        assert str(new_state) in error.message

    def test_get_allowed_transitions(self):
        """Test getting allowed transitions from a state."""
        allowed = StateMachine.get_allowed_transitions(OrderStatus.PENDING_PAYMENT, is_order=True)
        assert OrderStatus.PAID in allowed
        assert OrderStatus.CANCELLED in allowed
        assert len(allowed) == 2


class TestReturnStateMachine:
    """Test return state transitions."""

    # Valid transitions
    @pytest.mark.parametrize("current_state,new_state", [
        (ReturnStatus.REQUESTED, ReturnStatus.APPROVED),
        (ReturnStatus.REQUESTED, ReturnStatus.REJECTED),
        (ReturnStatus.APPROVED, ReturnStatus.IN_TRANSIT),
        (ReturnStatus.IN_TRANSIT, ReturnStatus.RECEIVED),
        (ReturnStatus.RECEIVED, ReturnStatus.COMPLETED),
    ])
    def test_valid_return_transitions(self, current_state, new_state):
        """Test that valid return transitions are allowed."""
        assert StateMachine.can_transition(current_state, new_state, is_order=False)
        # Should not raise exception
        StateMachine.validate_transition(current_state, new_state, is_order=False)

    # Invalid transitions
    @pytest.mark.parametrize("current_state,new_state", [
        (ReturnStatus.REQUESTED, ReturnStatus.IN_TRANSIT),
        (ReturnStatus.REQUESTED, ReturnStatus.RECEIVED),
        (ReturnStatus.REQUESTED, ReturnStatus.COMPLETED),
        (ReturnStatus.APPROVED, ReturnStatus.REQUESTED),
        (ReturnStatus.APPROVED, ReturnStatus.REJECTED),
        (ReturnStatus.APPROVED, ReturnStatus.RECEIVED),
        (ReturnStatus.APPROVED, ReturnStatus.COMPLETED),
        (ReturnStatus.REJECTED, ReturnStatus.REQUESTED),
        (ReturnStatus.REJECTED, ReturnStatus.APPROVED),
        (ReturnStatus.REJECTED, ReturnStatus.IN_TRANSIT),
        (ReturnStatus.REJECTED, ReturnStatus.RECEIVED),
        (ReturnStatus.REJECTED, ReturnStatus.COMPLETED),
        (ReturnStatus.IN_TRANSIT, ReturnStatus.REQUESTED),
        (ReturnStatus.IN_TRANSIT, ReturnStatus.APPROVED),
        (ReturnStatus.IN_TRANSIT, ReturnStatus.REJECTED),
        (ReturnStatus.IN_TRANSIT, ReturnStatus.COMPLETED),
        (ReturnStatus.RECEIVED, ReturnStatus.REQUESTED),
        (ReturnStatus.RECEIVED, ReturnStatus.APPROVED),
        (ReturnStatus.RECEIVED, ReturnStatus.REJECTED),
        (ReturnStatus.RECEIVED, ReturnStatus.IN_TRANSIT),
        (ReturnStatus.COMPLETED, ReturnStatus.REQUESTED),
        (ReturnStatus.COMPLETED, ReturnStatus.APPROVED),
        (ReturnStatus.COMPLETED, ReturnStatus.REJECTED),
        (ReturnStatus.COMPLETED, ReturnStatus.IN_TRANSIT),
        (ReturnStatus.COMPLETED, ReturnStatus.RECEIVED),
    ])
    def test_invalid_return_transitions(self, current_state, new_state):
        """Test that invalid return transitions are rejected."""
        assert not StateMachine.can_transition(current_state, new_state, is_order=False)
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            StateMachine.validate_transition(current_state, new_state, is_order=False)
        
        # Verify error details
        error = exc_info.value
        assert error.code == "INVALID_STATE_TRANSITION"
        assert str(current_state) in error.message
        assert str(new_state) in error.message

    def test_get_allowed_transitions(self):
        """Test getting allowed transitions from a state."""
        allowed = StateMachine.get_allowed_transitions(ReturnStatus.REQUESTED, is_order=False)
        assert ReturnStatus.APPROVED in allowed
        assert ReturnStatus.REJECTED in allowed
        assert len(allowed) == 2
