"""
Return request Pydantic schemas.
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator, ConfigDict
from app.services.state_machine import ReturnStatus


class ReturnItemRequest(BaseModel):
    """Item to be returned."""
    line_item_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class ReturnCreate(BaseModel):
    """Return request creation schema."""
    order_id: int = Field(..., gt=0)
    reason: str = Field(..., min_length=1, max_length=5000)
    requested_by: str = Field(..., min_length=1, max_length=100)
    items: List[ReturnItemRequest] = Field(..., min_items=1)
    refund_amount: Decimal = Field(..., ge=0, decimal_places=2)
    metadata: Optional[Dict[str, Any]] = None

    @validator("items")
    def validate_items(cls, v):
        if not v:
            raise ValueError("At least one item is required for return")
        return v


class ReturnResponse(BaseModel):
    """Return request response schema."""
    id: int
    order_id: int
    status: ReturnStatus
    reason: str
    requested_by: str
    items: List[Dict[str, Any]]
    refund_amount: Decimal
    refund_transaction_id: Optional[str]
    approved_by: Optional[str]
    rejection_reason: Optional[str]
    return_tracking_number: Optional[str]
    return_carrier: Optional[str]
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias="extra_metadata")
    created_at: datetime
    updated_at: datetime
    
    # Pydantic v2 config
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ReturnApproval(BaseModel):
    """Approve a return request."""
    approved_by: str = Field(..., min_length=1, max_length=100)
    metadata: Optional[Dict[str, Any]] = None
    notes: Optional[str] = Field(default=None, max_length=5000)


class ReturnRejection(BaseModel):
    """Reject a return request."""
    rejected_by: str = Field(..., min_length=1, max_length=100)
    rejection_reason: str = Field(..., min_length=1, max_length=5000)
    metadata: Optional[Dict[str, Any]] = None


class ReturnStateUpdate(BaseModel):
    """Return state transition request."""
    new_state: ReturnStatus = Field(..., description="Target state")
    actor: str = Field(..., min_length=1, max_length=100, description="User ID or SYSTEM")
    trigger: str = Field(default="API", max_length=100, description="Trigger source")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    notes: Optional[str] = Field(default=None, max_length=5000, description="Transition notes")


class ReturnShippingUpdate(BaseModel):
    """Update return shipping information."""
    return_tracking_number: str = Field(..., min_length=1, max_length=200)
    return_carrier: str = Field(..., min_length=1, max_length=100)
    metadata: Optional[Dict[str, Any]] = None
