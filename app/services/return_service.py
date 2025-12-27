"""
Return request service layer for business logic.
"""
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.return_request import ReturnRequest
from app.models.order import Order
from app.models.state_history import StateHistory
from app.schemas.return_request import ReturnCreate, ReturnResponse
from app.schemas.state_history import StateHistoryRecord
from app.services.state_machine import StateMachine, ReturnStatus
from app.services.audit_service import AuditService
from app.utils.exceptions import ResourceNotFoundError, InvalidStateTransitionError, ValidationError


class ReturnService:
    """Service for return request operations."""

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def create_return(
        self,
        return_data: ReturnCreate,
        ip_address: Optional[str] = None,
    ) -> ReturnResponse:
        """
        Create a new return request in REQUESTED state.
        
        Args:
            return_data: Return creation data
            ip_address: Client IP address for audit
            
        Returns:
            Created return request
            
        Raises:
            ValidationError: Order not found or invalid items
        """
        # Validate order exists
        order = self.db.query(Order).filter(Order.id == return_data.order_id).first()
        if not order:
            raise ValidationError(f"Order {return_data.order_id} not found")

        # TODO: Validate items exist in order and quantities are valid
        
        # Create return request
        return_request = ReturnRequest(
            order_id=return_data.order_id,
            status=ReturnStatus.REQUESTED,
            reason=return_data.reason,
            requested_by=return_data.requested_by,
            items=[item.model_dump() for item in return_data.items],
            refund_amount=return_data.refund_amount,
            metadata=return_data.metadata,
        )
        
        self.db.add(return_request)
        self.db.flush()

        # Record initial state in audit trail
        self.audit_service.record_state_change(
            return_request_id=return_request.id,
            previous_state=None,
            new_state=ReturnStatus.REQUESTED,
            actor=return_data.requested_by,
            trigger="API",
            ip_address=ip_address,
            metadata={"action": "return_requested"},
        )

        self.db.commit()
        self.db.refresh(return_request)
        
        return ReturnResponse.model_validate(return_request)

    def get_return(self, return_id: int) -> Optional[ReturnResponse]:
        """Get return request by ID."""
        return_request = self.db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
        if not return_request:
            return None
        return ReturnResponse.model_validate(return_request)

    def list_returns(
        self,
        order_id: Optional[int] = None,
        status: Optional[ReturnStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ReturnResponse], int]:
        """
        List return requests with filters and pagination.
        
        Returns:
            Tuple of (returns, total_count)
        """
        query = self.db.query(ReturnRequest)
        
        if order_id:
            query = query.filter(ReturnRequest.order_id == order_id)
        if status:
            query = query.filter(ReturnRequest.status == status)
        
        total = query.count()
        
        returns = query.order_by(ReturnRequest.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        return [ReturnResponse.model_validate(r) for r in returns], total

    def approve_return(
        self,
        return_id: int,
        approved_by: str,
        metadata: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> ReturnResponse:
        """
        Approve a return request (REQUESTED → APPROVED).
        
        Args:
            return_id: Return request ID
            approved_by: Admin user ID
            metadata: Additional context
            notes: Approval notes
            ip_address: Client IP
            
        Returns:
            Updated return request
            
        Raises:
            ResourceNotFoundError: Return not found
            InvalidStateTransitionError: Invalid transition
        """
        return_request = self.db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
        if not return_request:
            raise ResourceNotFoundError("ReturnRequest", return_id)

        # Validate transition
        StateMachine.validate_transition(
            return_request.status, ReturnStatus.APPROVED, is_order=False
        )

        # Update return
        previous_state = return_request.status
        return_request.status = ReturnStatus.APPROVED
        return_request.approved_by = approved_by

        self.audit_service.record_state_change(
            return_request_id=return_id,
            previous_state=previous_state,
            new_state=ReturnStatus.APPROVED,
            actor=approved_by,
            trigger="API",
            ip_address=ip_address,
            metadata=metadata,
            notes=notes,
        )

        self.db.commit()
        self.db.refresh(return_request)
        
        return ReturnResponse.model_validate(return_request)

    def reject_return(
        self,
        return_id: int,
        rejected_by: str,
        rejection_reason: str,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> ReturnResponse:
        """
        Reject a return request (REQUESTED → REJECTED).
        
        Args:
            return_id: Return request ID
            rejected_by: Admin user ID
            rejection_reason: Reason for rejection
            metadata: Additional context
            ip_address: Client IP
            
        Returns:
            Updated return request
            
        Raises:
            ResourceNotFoundError: Return not found
            InvalidStateTransitionError: Invalid transition
        """
        return_request = self.db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
        if not return_request:
            raise ResourceNotFoundError("ReturnRequest", return_id)

        # Validate transition
        StateMachine.validate_transition(
            return_request.status, ReturnStatus.REJECTED, is_order=False
        )

        # Update return
        previous_state = return_request.status
        return_request.status = ReturnStatus.REJECTED
        return_request.approved_by = rejected_by  # Store who rejected
        return_request.rejection_reason = rejection_reason

        self.audit_service.record_state_change(
            return_request_id=return_id,
            previous_state=previous_state,
            new_state=ReturnStatus.REJECTED,
            actor=rejected_by,
            trigger="API",
            ip_address=ip_address,
            metadata=metadata,
            notes=rejection_reason,
        )

        self.db.commit()
        self.db.refresh(return_request)
        
        return ReturnResponse.model_validate(return_request)

    def transition_state(
        self,
        return_id: int,
        new_state: ReturnStatus,
        actor: str,
        trigger: str = "API",
        metadata: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> ReturnResponse:
        """
        Transition return to new state with validation.
        
        Args:
            return_id: Return ID
            new_state: Target state
            actor: User ID or SYSTEM
            trigger: Source of transition
            metadata: Additional context
            notes: Transition notes
            ip_address: Client IP
            
        Returns:
            Updated return request
            
        Raises:
            ResourceNotFoundError: Return not found
            InvalidStateTransitionError: Invalid transition
        """
        return_request = self.db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
        if not return_request:
            raise ResourceNotFoundError("ReturnRequest", return_id)

        # Validate transition
        StateMachine.validate_transition(return_request.status, new_state, is_order=False)

        # Record state change
        previous_state = return_request.status
        return_request.status = new_state

        self.audit_service.record_state_change(
            return_request_id=return_id,
            previous_state=previous_state,
            new_state=new_state,
            actor=actor,
            trigger=trigger,
            ip_address=ip_address,
            metadata=metadata,
            notes=notes,
        )

        self.db.commit()
        self.db.refresh(return_request)

        # Trigger background jobs based on state
        if new_state == ReturnStatus.COMPLETED:
            from app.tasks.refund_tasks import process_refund
            process_refund.delay(return_id)
        
        return ReturnResponse.model_validate(return_request)

    def update_shipping(
        self,
        return_id: int,
        tracking_number: str,
        carrier: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ReturnResponse]:
        """Update return shipping information."""
        return_request = self.db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
        if not return_request:
            return None

        return_request.return_tracking_number = tracking_number
        return_request.return_carrier = carrier
        if metadata:
            return_request.metadata = {**(return_request.metadata or {}), **metadata}

        self.db.commit()
        self.db.refresh(return_request)
        
        return ReturnResponse.model_validate(return_request)

    def get_state_history(self, return_id: int) -> List[StateHistoryRecord]:
        """Get audit trail for a return request."""
        history = (
            self.db.query(StateHistory)
            .filter(StateHistory.return_request_id == return_id)
            .order_by(StateHistory.timestamp.asc())
            .all()
        )
        return [StateHistoryRecord.model_validate(h) for h in history]
