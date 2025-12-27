"""
Metrics endpoint for system statistics.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.order import Order
from app.models.return_request import ReturnRequest
from app.schemas.common import MetricsResponse
from app.config import settings
from app.core.security import get_api_key

router = APIRouter(dependencies=[Depends(get_api_key)])

@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(db: Session = Depends(get_db)) -> MetricsResponse:
    """
    Returns system metrics: order/return counts and status breakdown.
    """
    orders_total = db.query(Order).count()
    orders_by_status = {s: db.query(Order).filter(Order.status == s).count() for s in Order.__table__.columns.status.type.enums}
    returns_total = db.query(ReturnRequest).count()
    returns_by_status = {s: db.query(ReturnRequest).filter(ReturnRequest.status == s).count() for s in ReturnRequest.__table__.columns.status.type.enums}
    # Placeholder for performance metrics
    performance = {"avg_response_time_ms": 0, "p95_response_time_ms": 0}
    return MetricsResponse(
        orders={"total": orders_total, "by_status": orders_by_status},
        returns={"total": returns_total, "by_status": returns_by_status},
        performance=performance
    )
