"""
State history Pydantic schemas.
"""
from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_serializer


class StateHistoryRecord(BaseModel):
    """State history audit record."""
    id: int
    order_id: Optional[int]
    return_request_id: Optional[int]
    previous_state: Optional[str]
    new_state: str
    actor: str
    trigger: str
    timestamp: datetime
    ip_address: Optional[str]
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias="extra_metadata")
    notes: Optional[str]
    
    # Pydantic v2 config
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    @field_serializer("previous_state", when_used="always")
    def _serialize_previous_state(self, v):
        return v.value if isinstance(v, Enum) else v

    @field_serializer("new_state", when_used="always")
    def _serialize_new_state(self, v):
        return v.value if isinstance(v, Enum) else v


class StateHistoryResponse(BaseModel):
    """Response containing state history records."""
    history: list[StateHistoryRecord]
    total_count: int
