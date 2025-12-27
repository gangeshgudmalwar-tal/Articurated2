"""
Order API endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderStateUpdate,
    OrderShippingUpdate,
)
from app.schemas.common import PaginatedResponse, PaginationParams, PageInfo
from app.schemas.state_history import StateHistoryResponse
from app.services.order_service import OrderService
from app.services.state_machine import OrderStatus
from app.utils.exceptions import ResourceNotFoundError, InvalidStateTransitionError
from app.core.security import get_api_key

router = APIRouter(dependencies=[Depends(get_api_key)])


@router.post("/orders", response_model=OrderResponse, status_code=201)
async def create_order(
    order_data: OrderCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> OrderResponse:
    """
    Create a new order.
    
    Initial state: PENDING_PAYMENT
    """
    service = OrderService(db)
    order = service.create_order(order_data, ip_address=request.client.host)
    return order


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: Session = Depends(get_db)) -> OrderResponse:
    """Get order by ID."""
    service = OrderService(db)
    order = service.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return order


@router.get("/orders", response_model=PaginatedResponse[OrderResponse])
async def list_orders(
    customer_id: Optional[str] = None,
    status: Optional[OrderStatus] = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
) -> PaginatedResponse[OrderResponse]:
    """
    List orders with optional filters.
    
    Query parameters:
    - customer_id: Filter by customer
    - status: Filter by order status
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    """
    service = OrderService(db)
    orders, total = service.list_orders(
        customer_id=customer_id,
        status=status,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    
    total_pages = (total + pagination.page_size - 1) // pagination.page_size
    
    return PaginatedResponse(
        items=orders,
        page_info=PageInfo(
            page=pagination.page,
            page_size=pagination.page_size,
            total_items=total,
            total_pages=total_pages,
        ),
    )


@router.patch("/orders/{order_id}/state", response_model=OrderResponse)
async def update_order_state(
    order_id: int,
    state_update: OrderStateUpdate,
    request: Request,
    db: Session = Depends(get_db),
) -> OrderResponse:
    """
    Transition order to a new state.
    
    Validates state machine rules and records audit trail.
    """
    try:
        service = OrderService(db)
        order = service.transition_state(
            order_id=order_id,
            new_state=state_update.new_state,
            actor=state_update.actor,
            trigger=state_update.trigger,
            metadata=state_update.metadata,
            notes=state_update.notes,
            ip_address=request.client.host,
        )
        return order
    except ResourceNotFoundError as e:
        return JSONResponse(status_code=404, content=e.to_dict())
    except InvalidStateTransitionError as e:
        return JSONResponse(status_code=400, content=e.to_dict())


@router.patch("/orders/{order_id}/shipping", response_model=OrderResponse)
async def update_order_shipping(
    order_id: int,
    shipping_update: OrderShippingUpdate,
    db: Session = Depends(get_db),
) -> OrderResponse:
    """Update shipping information for an order."""
    service = OrderService(db)
    order = service.update_shipping(
        order_id=order_id,
        tracking_number=shipping_update.tracking_number,
        carrier=shipping_update.carrier,
        metadata=shipping_update.metadata,
    )
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return order


@router.get("/orders/{order_id}/audit", response_model=StateHistoryResponse)
async def get_order_audit(
    order_id: int,
    db: Session = Depends(get_db),
) -> StateHistoryResponse:
    """Alias endpoint for audit trail (legacy 'audit' path)."""
    service = OrderService(db)
    history = service.get_state_history(order_id)
    return StateHistoryResponse(history=history, total_count=len(history))


@router.get("/orders/{order_id}/history", response_model=StateHistoryResponse)
async def get_order_history(
    order_id: int,
    db: Session = Depends(get_db),
) -> StateHistoryResponse:
    """Get state transition history for an order."""
    service = OrderService(db)
    history = service.get_state_history(order_id)
    return StateHistoryResponse(history=history, total_count=len(history))
