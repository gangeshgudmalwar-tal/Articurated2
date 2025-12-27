"""
Custom exception classes for the application.
"""
from typing import Any, Dict, List, Optional


class ArtiCuratedException(Exception):
    """Base exception for all custom exceptions."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to API error response format."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class InvalidStateTransitionError(ArtiCuratedException):
    """Raised when an invalid state transition is attempted."""

    def __init__(
        self,
        current_state: str,
        requested_state: str,
        allowed_transitions: List[str],
    ):
        super().__init__(
            message=f"Cannot transition from {current_state} to {requested_state}",
            code="INVALID_STATE_TRANSITION",
            details={
                "current_state": current_state,
                "requested_state": requested_state,
                "allowed_transitions": allowed_transitions,
            },
        )


class ResourceNotFoundError(ArtiCuratedException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource_type: str, resource_id: Any):
        super().__init__(
            message=f"{resource_type} with ID {resource_id} not found",
            code="RESOURCE_NOT_FOUND",
            details={
                "resource_type": resource_type,
                "resource_id": str(resource_id),
            },
        )


class ValidationError(ArtiCuratedException):
    """Raised when request validation fails."""

    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else {}
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details=details,
        )


class PaymentError(ArtiCuratedException):
    """Raised when payment processing fails."""

    def __init__(self, message: str, transaction_id: Optional[str] = None):
        details = {"transaction_id": transaction_id} if transaction_id else {}
        super().__init__(
            message=message,
            code="PAYMENT_ERROR",
            details=details,
        )


class RetryableError(ArtiCuratedException):
    """Raised for errors that should trigger a retry."""

    def __init__(self, message: str, retry_count: int = 0):
        super().__init__(
            message=message,
            code="RETRYABLE_ERROR",
            details={"retry_count": retry_count},
        )
