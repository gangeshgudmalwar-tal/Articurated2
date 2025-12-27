"""
Order-related Pydantic schemas.
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator, ConfigDict
from app.services.state_machine import OrderStatus


class Address(BaseModel):
    """Address schema."""
    street: str = Field(..., min_length=1, max_length=500)
    city: str = Field(..., min_length=1, max_length=200)
    state: str = Field(..., min_length=2, max_length=100)
    postal_code: str = Field(..., min_length=1, max_length=20)
    country: str = Field(..., min_length=2, max_length=100)


class LineItemCreate(BaseModel):
    """Line item creation schema."""
    product_id: str = Field(..., min_length=1, max_length=100)
    product_name: str = Field(..., min_length=1, max_length=500)
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0, decimal_places=2)


class LineItemResponse(LineItemCreate):
    """Line item response schema."""
    id: int
    subtotal: Decimal
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias="extra_metadata")
    created_at: datetime
    updated_at: datetime
    
    # Pydantic v2 config
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class OrderCreate(BaseModel):
    """Order creation schema."""
    customer_id: str = Field(..., min_length=1, max_length=100)
    shipping_address: Address
    billing_address: Address
    payment_method: str = Field(..., min_length=1, max_length=50)
    line_items: List[LineItemCreate] = Field(..., min_items=1)
    metadata: Optional[Dict[str, Any]] = None

    @validator("line_items")
    def validate_line_items(cls, v):
        if not v:
            raise ValueError("At least one line item is required")
        return v


class OrderResponse(BaseModel):
    """Order response schema."""
    id: int
    customer_id: str
    status: OrderStatus
    shipping_address: Dict[str, Any]
    billing_address: Dict[str, Any]
    payment_method: str
    payment_transaction_id: Optional[str]
    tracking_number: Optional[str]
    carrier: Optional[str]
    subtotal: Decimal
    tax: Decimal
    shipping_cost: Decimal
    total: Decimal
    line_items: List[LineItemResponse]
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias="extra_metadata")
    created_at: datetime
    updated_at: datetime
    
    # Pydantic v2 config
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class OrderStateUpdate(BaseModel):
    """Order state transition request."""
    new_state: OrderStatus = Field(..., description="Target state")
    actor: str = Field(..., min_length=1, max_length=100, description="User ID or SYSTEM")
    trigger: str = Field(default="API", max_length=100, description="Trigger source")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    notes: Optional[str] = Field(default=None, max_length=5000, description="Transition notes")


class OrderShippingUpdate(BaseModel):
    """Update shipping information for an order."""
    tracking_number: str = Field(..., min_length=1, max_length=200)
    carrier: str = Field(..., min_length=1, max_length=100)
    metadata: Optional[Dict[str, Any]] = None
