"""
Return request API endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.return_request import (
    ReturnCreate,
    ReturnResponse,
    ReturnApproval,
    ReturnRejection,
    ReturnStateUpdate,
    ReturnShippingUpdate,
)
from app.schemas.common import PaginatedResponse, PaginationParams, PageInfo
from app.schemas.state_history import StateHistoryResponse
from app.services.return_service import ReturnService
from app.services.state_machine import ReturnStatus
from app.utils.exceptions import ResourceNotFoundError, InvalidStateTransitionError, ValidationError
from app.core.security import get_api_key

router = APIRouter(dependencies=[Depends(get_api_key)])


@router.post("/returns", response_model=ReturnResponse, status_code=201)
async def create_return(
    return_data: ReturnCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> ReturnResponse:
    """
    Create a new return request.
    
    Initial state: REQUESTED
    """
    try:
        service = ReturnService(db)
        return_request = service.create_return(return_data, ip_address=request.client.host)
        return return_request
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.get("/returns/{return_id}", response_model=ReturnResponse)
async def get_return(return_id: int, db: Session = Depends(get_db)) -> ReturnResponse:
    """Get return request by ID."""
    service = ReturnService(db)
    return_request = service.get_return(return_id)
    if not return_request:
        raise HTTPException(status_code=404, detail=f"Return request {return_id} not found")
    return return_request


@router.get("/returns", response_model=PaginatedResponse[ReturnResponse])
async def list_returns(
    order_id: Optional[int] = None,
    status: Optional[ReturnStatus] = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ReturnResponse]:
    """
    List return requests with optional filters.
    
    Query parameters:
    - order_id: Filter by order
    - status: Filter by return status
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    """
    service = ReturnService(db)
    returns, total = service.list_returns(
        order_id=order_id,
        status=status,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    
    total_pages = (total + pagination.page_size - 1) // pagination.page_size
    
    return PaginatedResponse(
        items=returns,
        page_info=PageInfo(
            page=pagination.page,
            page_size=pagination.page_size,
            total_items=total,
            total_pages=total_pages,
        ),
    )


@router.patch("/returns/{return_id}/approve", response_model=ReturnResponse)
async def approve_return(
    return_id: int,
    approval: ReturnApproval,
    request: Request,
    db: Session = Depends(get_db),
) -> ReturnResponse:
    """
    Approve a return request.
    
    Transitions state from REQUESTED to APPROVED.
    """
    try:
        service = ReturnService(db)
        return_request = service.approve_return(
            return_id=return_id,
            approved_by=approval.approved_by,
            metadata=approval.metadata,
            notes=approval.notes,
            ip_address=request.client.host,
        )
        return return_request
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.patch("/returns/{return_id}/reject", response_model=ReturnResponse)
async def reject_return(
    return_id: int,
    rejection: ReturnRejection,
    request: Request,
    db: Session = Depends(get_db),
) -> ReturnResponse:
    """
    Reject a return request.
    
    Transitions state from REQUESTED to REJECTED.
    """
    try:
        service = ReturnService(db)
        return_request = service.reject_return(
            return_id=return_id,
            rejected_by=rejection.rejected_by,
            rejection_reason=rejection.rejection_reason,
            metadata=rejection.metadata,
            ip_address=request.client.host,
        )
        return return_request
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.patch("/returns/{return_id}/state", response_model=ReturnResponse)
async def update_return_state(
    return_id: int,
    state_update: ReturnStateUpdate,
    request: Request,
    db: Session = Depends(get_db),
) -> ReturnResponse:
    """
    Transition return to a new state.
    
    Validates state machine rules and records audit trail.
    """
    try:
        service = ReturnService(db)
        return_request = service.transition_state(
            return_id=return_id,
            new_state=state_update.new_state,
            actor=state_update.actor,
            trigger=state_update.trigger,
            metadata=state_update.metadata,
            notes=state_update.notes,
            ip_address=request.client.host,
        )
        return return_request
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.to_dict())
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())


@router.patch("/returns/{return_id}/shipping", response_model=ReturnResponse)
async def update_return_shipping(
    return_id: int,
    shipping_update: ReturnShippingUpdate,
    db: Session = Depends(get_db),
) -> ReturnResponse:
    """Update return shipping information."""
    service = ReturnService(db)
    return_request = service.update_shipping(
        return_id=return_id,
        tracking_number=shipping_update.return_tracking_number,
        carrier=shipping_update.return_carrier,
        metadata=shipping_update.metadata,
    )
    if not return_request:
        raise HTTPException(status_code=404, detail=f"Return request {return_id} not found")
    return return_request


@router.get("/returns/{return_id}/history", response_model=StateHistoryResponse)
async def get_return_history(
    return_id: int,
    db: Session = Depends(get_db),
) -> StateHistoryResponse:
    """Get state transition history for a return request."""
    service = ReturnService(db)
    history = service.get_state_history(return_id)
    return StateHistoryResponse(history=history, total_count=len(history))
