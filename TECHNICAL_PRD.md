# Technical Product Requirements Document
## ArtiCurated Order Management System - Python Implementation

---

**Version:** 1.0  
**Last Updated:** December 2024  
**Document Owner:** Lead Technical Engineer  
**Status:** Active  
**Development Model:** Individual Developer + AI-Assisted Tooling

---

## 1. Executive Summary

This technical PRD defines the implementation strategy for the ArtiCurated Order Management System using a Python-based technology stack. The system will be developed by an individual engineer leveraging AI-assisted development tools to maximize productivity and code quality.

### Key Technical Decisions

- **Language:** Python 3.11+
- **Framework:** FastAPI
- **Database:** PostgreSQL 15+
- **Background Processing:** Celery + Redis
- **Deployment:** Docker Compose

---

## 2. Technology Stack Rationale

### 2.1 Core Framework: FastAPI

**Selected:** FastAPI 0.104+

**Rationale:**
- **Performance Requirements Met:** Async-native architecture easily achieves <200ms p95 response time requirement
- **Auto-Generated Documentation:** Built-in OpenAPI/Swagger UI reduces documentation overhead for solo developer
- **Type Safety:** Full type hints + Pydantic validation catches errors at development time (critical for AI-assisted coding)
- **JSON Schema Native:** Pydantic models directly support PRD requirement for JSON Schema validation
- **Developer Productivity:** Less boilerplate than Flask, modern async/await patterns
- **AI Assistant Friendly:** Clear, explicit type hints improve AI code generation accuracy

**Why Not Flask:**
- Requires additional libraries for async, validation, and auto-documentation
- More boilerplate for error handling and request validation
- Less type-safe, reducing effectiveness of AI-assisted development

**Why Not Django:**
- Over-engineered for API-only service (ORM, admin, templates not needed)
- Opinionated structure conflicts with state machine domain model requirements
- Slower startup and heavier resource footprint

---

### 2.2 Database: PostgreSQL 15+

**Selected:** PostgreSQL 15.4

**Rationale:**
- **ACID Compliance:** Critical for state machine integrity and audit trail immutability
- **JSON/JSONB Support:** Perfect for flexible metadata, addresses, and audit logs without schema migrations
- **Row-Level Locking:** Prevents race conditions in concurrent state transitions
- **Mature Ecosystem:** Excellent SQLAlchemy support, proven at scale
- **Advanced Indexing:** GIN indexes for JSON queries, partial indexes for state-based queries
- **Point-in-Time Recovery:** Meets 6-hour backup requirement from PRD

**Why Not MySQL:**
- Weaker JSON support and indexing capabilities
- Less robust transaction isolation for complex state machines

**Why Not MongoDB:**
- PRD requires relational data (orders → line items, orders → returns)
- Audit trail needs strong consistency guarantees

---

### 2.3 ORM: SQLAlchemy 2.0+

**Selected:** SQLAlchemy 2.0.23

**Rationale:**
- **Mature & Battle-Tested:** Industry standard Python ORM
- **Migration Support:** Alembic for database versioning (required for Docker deployment)
- **Complex Relationships:** Handles 1:N, 1:1 relationships in data model
- **Type Hints:** SQLAlchemy 2.0 modernized with full type annotation support
- **Connection Pooling:** Built-in pool management for performance requirements

**Integration with FastAPI:**
- FastAPI + SQLAlchemy 2.0 async sessions pattern well-documented
- Pydantic models separate from SQLAlchemy models (clean architecture)

---

### 2.4 Background Processing: Celery + Redis

**Selected:** 
- Celery 5.3+
- Redis 7.2 (message broker + cache)

**Rationale for Celery:**
- **Retry Policies:** Built-in exponential backoff matches PRD requirements (3 retries for invoices, 5 for refunds)
- **Task Routing:** Separate queues for invoices vs. refunds (different SLAs)
- **Monitoring:** Flower dashboard for task visibility (critical for solo developer)
- **Scheduled Tasks:** Cron-like scheduling for daily reports, return expiration
- **Result Backend:** Track task success/failure for audit trail
- **Battle-Tested:** Industry standard, extensive documentation

**Rationale for Redis:**
- **Dual Purpose:** Message broker for Celery + cache for API responses
- **Performance:** In-memory speed for background job pickup (<30s latency requirement)
- **Simple Setup:** Single Docker container, minimal configuration
- **Pub/Sub:** Future webhook/notification support

**Why Not ARQ:**
- Smaller ecosystem, less mature
- Limited monitoring tools compared to Flower
- Celery's retry/routing features more production-ready

**Why Not RabbitMQ:**
- Overkill for single-service monolith
- Redis simpler for solo developer, fewer moving parts

---

### 2.5 Additional Libraries & Tools

#### PDF Generation: WeasyPrint
- HTML/CSS templates → PDF (designer-friendly, no coding for layout changes)
- Pure Python, no external dependencies (simpler Docker image)
- Professional output quality for invoices

**Alternatives Considered:**
- ReportLab: More coding, less flexible for design changes
- wkhtmltopdf: External binary, harder to containerize

#### Email: SMTP + Jinja2 Templates
- **Development:** MailHog (mock SMTP server in Docker Compose)
- **Production:** Python smtplib → SendGrid/AWS SES (config swap)
- Jinja2 for HTML email templates

#### Storage: Filesystem → S3-Compatible
- **Development:** Local filesystem mounted volume
- **Production Ready:** boto3 library (works with AWS S3, MinIO, Azure Blob)
- Configuration-driven swap (no code changes)

#### Authentication: python-jose + passlib
- JWT token generation/validation (API keys or user tokens)
- bcrypt password hashing (if user auth added later)

#### Configuration: Pydantic Settings
- Environment variable validation with type checking
- Separate dev/test/prod configs
- AI-assistant friendly (typed settings prevent config errors)

#### Testing Stack:
- **pytest 7.4+**: Standard Python testing
- **pytest-asyncio**: Async test support for FastAPI
- **httpx**: FastAPI test client
- **coverage.py**: Code coverage >80% requirement
- **Factory Boy**: Test data generation for orders/returns
- **pytest-mock**: Mock external services (payment gateway, email)

#### Monitoring & Observability:
- **prometheus-client**: Metrics export (response times, state transitions)
- **structlog**: Structured JSON logging for centralized log aggregation
- **sentry-sdk**: Error tracking (optional, but recommended for solo dev)

---

## 3. System Architecture

### 3.1 Service Components

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Compose Network                  │
│                                                               │
│  ┌──────────────┐      ┌──────────────┐     ┌────────────┐ │
│  │   FastAPI    │◄─────┤  PostgreSQL  │     │   Redis    │ │
│  │   API Server │      │   Database   │     │  (Broker)  │ │
│  │   (Port 8000)│      └──────────────┘     └────────────┘ │
│  └──────┬───────┘              ▲                    ▲       │
│         │                      │                    │       │
│         │ Publish Jobs         │                    │       │
│         ▼                      │                    │       │
│  ┌──────────────┐             │                    │       │
│  │   Celery     │─────────────┴────────────────────┘       │
│  │   Worker     │  (Consume Jobs & DB Updates)             │
│  │              │                                           │
│  └──────┬───────┘                                           │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐      ┌──────────────┐                   │
│  │  Blob Storage│      │   MailHog    │                   │
│  │  (Invoices)  │      │  (Dev Email) │                   │
│  └──────────────┘      └──────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Request Flow Examples

#### Order State Transition Flow:
```
1. Client → POST /api/v1/orders/:id/state {new_state: "PAID"}
2. FastAPI validates request (Pydantic)
3. State machine validates transition (PENDING_PAYMENT → PAID allowed?)
4. Begin database transaction:
   a. Update order.status = "PAID"
   b. Insert audit record (immutable)
   c. Commit transaction
5. Publish Celery task (if SHIPPED → trigger invoice job)
6. Return 200 OK with updated order
```

#### Background Job Flow (Invoice Generation):
```
1. Order transitions to SHIPPED
2. FastAPI publishes: generate_invoice.delay(order_id)
3. Celery worker picks up task (<30s)
4. Worker:
   a. Fetch order from DB
   b. Render HTML template
   c. WeasyPrint → PDF
   d. Save to blob storage
   e. Send email via SMTP
   f. Log success/failure
   g. Retry on failure (3x exponential backoff)
```

---

## 4. Project Structure

```
articurated-order-management/
├── docker-compose.yml              # All services definition
├── Dockerfile                      # FastAPI + Celery image
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── alembic.ini                     # Database migration config
├── pytest.ini                      # Test configuration
├── README.md                       # Setup & run instructions
├── TECHNICAL_PRD.md               # This document
├── Updated_PRD.md                 # Business requirements
├── WORKFLOW_DESIGN.md             # State diagrams (to be created)
├── API-SPECIFICATION.yml          # OpenAPI spec (auto-generated)
│
├── alembic/                       # Database migrations
│   ├── versions/
│   │   └── 001_initial_schema.py
│   └── env.py
│
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── config.py                  # Pydantic settings
│   ├── database.py                # SQLAlchemy session management
│   ├── dependencies.py            # FastAPI dependencies (DB, auth)
│   │
│   ├── api/                       # API routes
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── orders.py          # Order endpoints
│   │   │   ├── returns.py         # Return endpoints
│   │   │   ├── health.py          # Health check
│   │   │   └── metrics.py         # Metrics endpoint
│   │   └── deps.py                # Route dependencies
│   │
│   ├── models/                    # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── order.py               # Order + OrderLineItem
│   │   ├── return_request.py      # Return entity
│   │   ├── state_history.py       # Audit trail
│   │   └── base.py                # Base model class
│   │
│   ├── schemas/                   # Pydantic models (API contracts)
│   │   ├── __init__.py
│   │   ├── order.py               # OrderCreate, OrderResponse, etc.
│   │   ├── return_request.py      # ReturnCreate, ReturnResponse
│   │   ├── state_history.py       # AuditRecord
│   │   └── common.py              # Shared schemas (Pagination, Error)
│   │
│   ├── services/                  # Business logic layer
│   │   ├── __init__.py
│   │   ├── order_service.py       # Order CRUD + state transitions
│   │   ├── return_service.py      # Return CRUD + workflow
│   │   ├── state_machine.py       # State validation logic
│   │   ├── audit_service.py       # Audit trail management
│   │   └── payment_gateway.py     # Mock payment integration
│   │
│   ├── tasks/                     # Celery tasks
│   │   ├── __init__.py
│   │   ├── celery_app.py          # Celery instance
│   │   ├── invoice_tasks.py       # Invoice generation
│   │   ├── refund_tasks.py        # Refund processing
│   │   └── notification_tasks.py  # Email notifications
│   │
│   ├── utils/                     # Utilities
│   │   ├── __init__.py
│   │   ├── invoice_generator.py   # PDF generation
│   │   ├── email_sender.py        # SMTP email logic
│   │   ├── storage.py             # Blob storage abstraction
│   │   └── exceptions.py          # Custom exceptions
│   │
│   └── core/                      # Core functionality
│       ├── __init__.py
│       ├── security.py            # JWT, API key validation
│       ├── logging.py             # Structured logging setup
│       └── monitoring.py          # Prometheus metrics
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures (DB, client)
│   ├── factories.py               # Factory Boy factories
│   │
│   ├── unit/
│   │   ├── test_state_machine.py  # State transition validation
│   │   ├── test_order_service.py  # Order business logic
│   │   ├── test_return_service.py # Return business logic
│   │   └── test_invoice_gen.py    # PDF generation
│   │
│   ├── integration/
│   │   ├── test_order_api.py      # Order endpoints
│   │   ├── test_return_api.py     # Return endpoints
│   │   ├── test_background_jobs.py # Celery tasks
│   │   └── test_audit_trail.py    # Audit queries
│   │
│   └── e2e/
│       ├── test_order_lifecycle.py    # Full order flow
│       └── test_return_workflow.py    # Full return flow
│
├── storage/                       # Local blob storage (dev)
│   └── invoices/
│
└── templates/                     # Email & PDF templates
    ├── emails/
    │   ├── order_confirmation.html
    │   ├── order_shipped.html
    │   ├── return_approved.html
    │   └── refund_processed.html
    └── invoices/
        └── invoice_template.html
```

---

## 5. Database Schema Implementation

### 5.1 SQLAlchemy Models

#### Order Model (`app/models/order.py`):
```python
from sqlalchemy import Column, String, Numeric, JSON, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(Enum(OrderStatus), nullable=False, index=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    payment_method = Column(String(50))
    payment_transaction_id = Column(String(100))
    shipping_address = Column(JSON, nullable=False)
    billing_address = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(String(500), nullable=True)
    
    # Relationships
    line_items = relationship("OrderLineItem", back_populates="order", cascade="all, delete-orphan")
    return_request = relationship("ReturnRequest", back_populates="order", uselist=False)
    state_history = relationship("StateHistory", foreign_keys="[StateHistory.entity_id]", 
                                 primaryjoin="and_(Order.id==StateHistory.entity_id, StateHistory.entity_type=='ORDER')")
```

#### State History Model (`app/models/state_history.py`):
```python
class StateHistory(Base):
    __tablename__ = "state_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(Enum("ORDER", "RETURN", name="entity_type_enum"), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    previous_state = Column(String(50), nullable=False)
    new_state = Column(String(50), nullable=False)
    actor_id = Column(UUID(as_uuid=True), nullable=True)
    actor_type = Column(Enum("USER", "SYSTEM", name="actor_type_enum"), nullable=False)
    trigger = Column(String(100), nullable=False)  # "API_CALL", "BACKGROUND_JOB", "WEBHOOK"
    metadata = Column(JSON, default={})
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Composite index for efficient queries
    __table_args__ = (
        Index('idx_entity_history', 'entity_type', 'entity_id', 'created_at'),
    )
```

### 5.2 Alembic Migrations

**Migration Strategy:**
- Initial migration: Create all tables with indexes
- Subsequent migrations: Version-controlled schema changes
- Seed data: Separate management command (not in migrations)

**Example Migration (`alembic/versions/001_initial_schema.py`):**
```python
def upgrade():
    # Create custom enums
    op.execute("CREATE TYPE order_status AS ENUM ('PENDING_PAYMENT', 'PAID', 'PROCESSING_IN_WAREHOUSE', 'SHIPPED', 'DELIVERED', 'CANCELLED')")
    op.execute("CREATE TYPE return_status AS ENUM ('REQUESTED', 'APPROVED', 'REJECTED', 'IN_TRANSIT', 'RECEIVED', 'COMPLETED')")
    
    # Create orders table
    op.create_table('orders', ...)
    
    # Create indexes
    op.create_index('idx_orders_status', 'orders', ['status'])
    op.create_index('idx_orders_customer', 'orders', ['customer_id'])
```

---

## 6. Test-Driven Development Strategy

### 6.1 TDD Principles

**This project uses Test-Driven Development (TDD) as the primary development methodology:**

```yaml
core_principles:
  tests_first: Write tests before implementation code
  behavior_driven: Test what code does, not how it does it
  high_coverage: Minimum 85% code coverage, target 90%+
  integration_testing: Test complete workflows end-to-end
  security_testing: Test for vulnerabilities and injection attacks
  performance_testing: Validate SLAs on all critical paths
```

**Benefits for this project:**
- **State Machine Confidence:** 95%+ coverage of state transitions ensures no invalid transitions escape
- **Audit Trail Integrity:** Tests verify audit records are created correctly
- **API Contract Validation:** Pydantic schemas + tests ensure API correctness
- **Regression Prevention:** Comprehensive test suite catches regressions early
- **Refactoring Safety:** High coverage enables fearless refactoring
- **AI-Assisted Development:** Clear tests improve AI code generation quality

### 6.2 Testing Layers

```
Layer 1: Unit Tests (95%+ coverage)
├── Individual functions (OrderService.create_order)
├── State machine transitions
├── Calculation logic (totals, refunds)
└── Input validation

Layer 2: Integration Tests (90%+ coverage)
├── API endpoints with database
├── Celery task execution
├── Email/notification sending
└── Database transactions

Layer 3: E2E Tests (95%+ coverage)
├── Complete order lifecycle
├── Return workflow
├── Invoice generation + email
└── Refund processing

Layer 4: Performance Tests
├── API response times (< 200ms p95)
├── Database query performance
├── Celery task execution time
└── State transition speed

Layer 5: Security Tests
├── SQL injection prevention
├── XSS prevention
├── Input validation
└── Error message disclosure
```

### 6.3 Coverage Requirements by Component

```yaml
coverage_targets:
  services:
    order_service.py: 90%  # Critical business logic
    return_service.py: 90%
    state_machine.py: 95%   # Must be bulletproof
    audit_service.py: 85%
  
  api:
    orders.py: 85%
    returns.py: 85%
    health.py: 100%
  
  models:
    order.py: 90%
    return_request.py: 90%
    state_history.py: 85%
  
  tasks:
    invoice_tasks.py: 85%
    refund_tasks.py: 85%
    notification_tasks.py: 75%

overall_minimum: 85%
overall_target: 90%
```

### 6.4 Test Execution

**Run all tests with coverage:**
```bash
pytest --cov=app --cov-report=html --cov-report=term-missing

# Run by test level
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
pytest -m e2e                   # E2E tests only
pytest -m performance           # Performance tests only

# Run in parallel (faster CI)
pytest -n auto

# Generate coverage report
pytest --cov=app --cov-report=html
# Open htmlcov/index.html
```

**CI/CD Integration:**
- All tests must pass before merge
- Coverage must be >= 85%
- Performance tests must show SLA compliance
- Security tests must have no HIGH/CRITICAL findings

### 6.5 Implementation Guide

**For each feature, follow this workflow:**

1. **Write failing test** - Captures the requirement
2. **Write minimal code** - Makes test pass
3. **Refactor** - Improve quality while tests pass
4. **Verify coverage** - Ensure >= 85% for the component
5. **Integrate** - Run full test suite before merging

**Example TDD Cycle:**

```python
# Step 1: Write test
def test_partial_refund_calculation():
    service = RefundService()
    result = service.calculate_partial_refund(100.00, 50.0)
    assert result == 50.00

# Step 2: Write code
class RefundService:
    def calculate_partial_refund(self, amount: float, percent: float) -> float:
        return amount * (percent / 100)

# Step 3: Refactor
class RefundService:
    def calculate_partial_refund(self, amount: float, percent: float) -> float:
        """Calculate partial refund amount.
        
        Args:
            amount: Original amount in dollars
            percent: Refund percentage (0-100)
            
        Returns:
            Refund amount, rounded to 2 decimals
            
        Raises:
            ValueError: If percent outside 0-100
        """
        if not 0 <= percent <= 100:
            raise ValueError("Percent must be 0-100")
        return round(amount * (percent / 100), 2)

# Step 4: Add edge case tests
def test_partial_refund_validation():
    service = RefundService()
    with pytest.raises(ValueError):
        service.calculate_partial_refund(100, 150)

# Step 5: Verify coverage
# pytest --cov=app tests/unit/test_refund_service.py
# Coverage: 95% ✅
```

**Reference Documentation:**
- Full TDD framework: [`.github/docs/TDD_FRAMEWORK.md`](../.github/docs/TDD_FRAMEWORK.md)
- Test patterns: See `tests/` directory for examples
- Test fixtures: `tests/conftest.py` and `tests/factories.py`

---

## 7. State Machine Implementation

### 6.1 State Definitions (`app/services/state_machine.py`)

```python
from enum import Enum
from typing import Dict, Set

class OrderStatus(str, Enum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"
    PROCESSING_IN_WAREHOUSE = "PROCESSING_IN_WAREHOUSE"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"

class ReturnStatus(str, Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    IN_TRANSIT = "IN_TRANSIT"
    RECEIVED = "RECEIVED"
    COMPLETED = "COMPLETED"

# State transition rules from PRD
ORDER_TRANSITIONS: Dict[OrderStatus, Set[OrderStatus]] = {
    OrderStatus.PENDING_PAYMENT: {OrderStatus.PAID, OrderStatus.CANCELLED},
    OrderStatus.PAID: {OrderStatus.PROCESSING_IN_WAREHOUSE, OrderStatus.CANCELLED},
    OrderStatus.PROCESSING_IN_WAREHOUSE: {OrderStatus.SHIPPED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),  # Terminal state (except for returns)
    OrderStatus.CANCELLED: set(),  # Terminal state
}

RETURN_TRANSITIONS: Dict[ReturnStatus, Set[ReturnStatus]] = {
    ReturnStatus.REQUESTED: {ReturnStatus.APPROVED, ReturnStatus.REJECTED},
    ReturnStatus.APPROVED: {ReturnStatus.IN_TRANSIT},
    ReturnStatus.REJECTED: set(),  # Terminal state
    ReturnStatus.IN_TRANSIT: {ReturnStatus.RECEIVED},
    ReturnStatus.RECEIVED: {ReturnStatus.COMPLETED},
    ReturnStatus.COMPLETED: set(),  # Terminal state
}

class StateMachine:
    @staticmethod
    def validate_order_transition(current: OrderStatus, new: OrderStatus) -> bool:
        """Validate if order state transition is allowed."""
        allowed = ORDER_TRANSITIONS.get(current, set())
        return new in allowed
    
    @staticmethod
    def validate_return_transition(current: ReturnStatus, new: ReturnStatus) -> bool:
        """Validate if return state transition is allowed."""
        allowed = RETURN_TRANSITIONS.get(current, set())
        return new in allowed
    
    @staticmethod
    def get_allowed_order_transitions(current: OrderStatus) -> Set[OrderStatus]:
        """Get list of allowed transitions from current state."""
        return ORDER_TRANSITIONS.get(current, set())
```

### 6.2 State Transition with Audit Trail

```python
# app/services/order_service.py
from app.services.state_machine import StateMachine, OrderStatus
from app.services.audit_service import AuditService
from app.utils.exceptions import InvalidStateTransitionError

class OrderService:
    def __init__(self, db: Session, audit_service: AuditService):
        self.db = db
        self.audit = audit_service
    
    async def transition_state(
        self, 
        order_id: UUID, 
        new_state: OrderStatus,
        actor_id: UUID | None,
        trigger: str,
        metadata: dict = {},
        ip_address: str | None = None
    ) -> Order:
        """
        Transition order to new state with validation and audit trail.
        
        Raises:
            InvalidStateTransitionError: If transition is not allowed
        """
        order = self.db.query(Order).filter(Order.id == order_id).with_for_update().first()
        
        if not order:
            raise OrderNotFoundError(order_id)
        
        # Validate transition
        if not StateMachine.validate_order_transition(order.status, new_state):
            allowed = StateMachine.get_allowed_order_transitions(order.status)
            raise InvalidStateTransitionError(
                current_state=order.status,
                requested_state=new_state,
                allowed_transitions=list(allowed)
            )
        
        # Begin transaction (implicit with session)
        previous_state = order.status
        order.status = new_state
        order.updated_at = datetime.utcnow()
        
        # Create immutable audit record
        self.audit.record_state_change(
            entity_type="ORDER",
            entity_id=order_id,
            previous_state=previous_state,
            new_state=new_state,
            actor_id=actor_id,
            actor_type="USER" if actor_id else "SYSTEM",
            trigger=trigger,
            metadata=metadata,
            ip_address=ip_address
        )
        
        self.db.commit()
        
        # Trigger background jobs if needed
        if new_state == OrderStatus.SHIPPED:
            from app.tasks.invoice_tasks import generate_invoice
            generate_invoice.delay(str(order_id))
        
        return order
```

---

## 8. API Implementation Patterns

### 7.1 FastAPI Endpoint Example

```python
# app/api/v1/orders.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.schemas.order import OrderStateUpdate, OrderResponse, ErrorResponse
from app.services.order_service import OrderService
from app.api.deps import get_order_service, get_current_user

router = APIRouter(prefix="/orders", tags=["orders"])

@router.patch(
    "/{order_id}/state",
    response_model=OrderResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse}
    }
)
async def update_order_state(
    order_id: UUID,
    state_update: OrderStateUpdate,
    request: Request,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """
    Transition order to a new state.
    
    Validates state transition rules before applying change.
    Records audit trail entry for compliance.
    """
    try:
        order = await order_service.transition_state(
            order_id=order_id,
            new_state=state_update.new_state,
            actor_id=current_user.id,
            trigger="API_CALL",
            metadata={"reason": state_update.reason},
            ip_address=request.client.host
        )
        return order
    except InvalidStateTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "INVALID_STATE_TRANSITION",
                    "message": str(e),
                    "details": {
                        "current_state": e.current_state,
                        "requested_state": e.requested_state,
                        "allowed_transitions": e.allowed_transitions
                    }
                }
            }
        )
```

### 7.2 Pydantic Schemas

```python
# app/schemas/order.py
from pydantic import BaseModel, Field, validator
from datetime import datetime
from uuid import UUID

class OrderStateUpdate(BaseModel):
    new_state: OrderStatus
    reason: str | None = Field(None, max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "new_state": "PAID",
                "reason": "Payment confirmed via Stripe"
            }
        }

class OrderResponse(BaseModel):
    id: UUID
    order_number: str
    status: OrderStatus
    total_amount: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # SQLAlchemy model compatibility

class ErrorResponse(BaseModel):
    error: dict[str, Any]
```

---

## 9. Background Jobs Implementation

### 8.1 Celery Configuration

```python
# app/tasks/celery_app.py
from celery import Celery
from app.config import settings

celery_app = Celery(
    "articurated_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.invoice_tasks",
        "app.tasks.refund_tasks",
        "app.tasks.notification_tasks"
    ]
)

# Task routing
celery_app.conf.task_routes = {
    "app.tasks.invoice_tasks.*": {"queue": "invoices"},
    "app.tasks.refund_tasks.*": {"queue": "refunds"},
    "app.tasks.notification_tasks.*": {"queue": "notifications"}
}

# Retry configuration
celery_app.conf.task_acks_late = True
celery_app.conf.task_reject_on_worker_lost = True
celery_app.conf.worker_prefetch_multiplier = 1  # One task at a time for reliability
```

### 8.2 Invoice Generation Task

```python
# app/tasks/invoice_tasks.py
from celery import Task
from celery.utils.log import get_task_logger
from app.tasks.celery_app import celery_app
from app.utils.invoice_generator import InvoiceGenerator
from app.utils.email_sender import EmailSender
from app.utils.storage import StorageService

logger = get_task_logger(__name__)

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    retry_backoff=True,
    retry_backoff_max=600,  # 10 minutes
    retry_jitter=True
)
def generate_invoice(self: Task, order_id: str):
    """
    Generate PDF invoice for shipped order.
    
    Retry policy: 3 retries with exponential backoff (matches PRD)
    SLA: Process within 5 minutes of SHIPPED state
    """
    try:
        logger.info(f"Generating invoice for order {order_id}")
        
        # Fetch order from database
        from app.database import SessionLocal
        db = SessionLocal()
        order = db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            logger.error(f"Order {order_id} not found")
            return {"status": "error", "message": "Order not found"}
        
        # Generate PDF
        generator = InvoiceGenerator()
        pdf_content = generator.generate(order)
        
        # Store in blob storage
        storage = StorageService()
        invoice_path = f"invoices/{order.order_number}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
        storage.save(invoice_path, pdf_content)
        
        # Send email
        email_sender = EmailSender()
        email_sender.send_invoice(
            to=order.customer_email,
            order_number=order.order_number,
            invoice_attachment=pdf_content
        )
        
        logger.info(f"Invoice generated successfully for order {order_id}")
        return {"status": "success", "invoice_path": invoice_path}
        
    except Exception as exc:
        logger.error(f"Invoice generation failed: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc)
```

### 8.3 Refund Processing Task

```python
# app/tasks/refund_tasks.py
@celery_app.task(
    bind=True,
    max_retries=5,  # PRD: 5 retries for refunds
    default_retry_delay=120,
    retry_backoff=True,
    retry_backoff_max=1800,  # 30 minutes
    retry_jitter=True
)
def process_refund(self: Task, return_id: str):
    """
    Process refund for completed return.
    
    Retry policy: 5 retries with exponential backoff (matches PRD)
    SLA: Process within 2 hours of COMPLETED state
    Alert on final failure.
    """
    try:
        logger.info(f"Processing refund for return {return_id}")
        
        db = SessionLocal()
        return_request = db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
        
        if not return_request:
            logger.error(f"Return {return_id} not found")
            return {"status": "error", "message": "Return not found"}
        
        # Call payment gateway
        from app.services.payment_gateway import PaymentGateway
        gateway = PaymentGateway()
        
        refund_response = gateway.process_refund(
            order_id=return_request.order_id,
            amount=return_request.refund_amount,
            payment_token=return_request.order.payment_transaction_id
        )
        
        # Update return record with transaction ID
        return_request.refund_transaction_id = refund_response["transaction_id"]
        db.commit()
        
        # Send confirmation email
        EmailSender().send_refund_confirmation(
            to=return_request.order.customer_email,
            order_number=return_request.order.order_number,
            refund_amount=return_request.refund_amount
        )
        
        logger.info(f"Refund processed successfully for return {return_id}")
        return {"status": "success", "transaction_id": refund_response["transaction_id"]}
        
    except Exception as exc:
        logger.error(f"Refund processing failed: {exc}")
        
        # Alert on final retry
        if self.request.retries >= self.max_retries:
            logger.critical(f"FINAL RETRY FAILED for return {return_id} - ALERT REQUIRED")
            # TODO: Send alert to monitoring system (PagerDuty, Slack, etc.)
        
        raise self.retry(exc=exc)
```

---

## 10. Testing Strategy

### 9.1 Test Coverage Requirements

**PRD Requirement:** >80% code coverage

**Coverage Breakdown:**
- State machine: 100% (critical business logic)
- API endpoints: >90%
- Service layer: >85%
- Background jobs: >80%
- Utilities: >70%

### 9.2 Pytest Configuration

```python
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
asyncio_mode = auto
```

### 9.3 Test Fixtures

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# Test database
SQLALCHEMY_TEST_DATABASE_URL = "postgresql://test:test@localhost:5433/test_db"
test_engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=test_engine)

@pytest.fixture(scope="function")
def db_session():
    """Create clean database for each test."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI test client with test database."""
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

### 9.4 State Machine Tests (Example)

```python
# tests/unit/test_state_machine.py
import pytest
from app.services.state_machine import StateMachine, OrderStatus

class TestOrderStateMachine:
    """Test all valid and invalid order state transitions."""
    
    def test_pending_to_paid_allowed(self):
        assert StateMachine.validate_order_transition(
            OrderStatus.PENDING_PAYMENT, 
            OrderStatus.PAID
        ) is True
    
    def test_pending_to_cancelled_allowed(self):
        assert StateMachine.validate_order_transition(
            OrderStatus.PENDING_PAYMENT, 
            OrderStatus.CANCELLED
        ) is True
    
    def test_shipped_to_paid_forbidden(self):
        """PRD: No reverse transitions allowed."""
        assert StateMachine.validate_order_transition(
            OrderStatus.SHIPPED, 
            OrderStatus.PAID
        ) is False
    
    def test_delivered_to_processing_forbidden(self):
        assert StateMachine.validate_order_transition(
            OrderStatus.DELIVERED, 
            OrderStatus.PROCESSING_IN_WAREHOUSE
        ) is False
    
    @pytest.mark.parametrize("current,new,expected", [
        (OrderStatus.PENDING_PAYMENT, OrderStatus.PAID, True),
        (OrderStatus.PAID, OrderStatus.PROCESSING_IN_WAREHOUSE, True),
        (OrderStatus.PROCESSING_IN_WAREHOUSE, OrderStatus.SHIPPED, True),
        (OrderStatus.SHIPPED, OrderStatus.DELIVERED, True),
        (OrderStatus.PAID, OrderStatus.CANCELLED, True),
        # Invalid transitions
        (OrderStatus.SHIPPED, OrderStatus.PAID, False),
        (OrderStatus.DELIVERED, OrderStatus.CANCELLED, False),
        (OrderStatus.PROCESSING_IN_WAREHOUSE, OrderStatus.PENDING_PAYMENT, False),
    ])
    def test_all_transitions(self, current, new, expected):
        """Comprehensive state transition matrix test."""
        assert StateMachine.validate_order_transition(current, new) is expected
```

### 9.5 Integration Test Example

```python
# tests/integration/test_order_api.py
def test_order_state_transition_success(client, db_session):
    """Test successful order state transition via API."""
    # Create order
    order = OrderFactory(status=OrderStatus.PENDING_PAYMENT)
    db_session.add(order)
    db_session.commit()
    
    # Transition to PAID
    response = client.patch(
        f"/api/v1/orders/{order.id}/state",
        json={"new_state": "PAID", "reason": "Payment confirmed"}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "PAID"
    
    # Verify audit trail created
    audit_records = db_session.query(StateHistory).filter(
        StateHistory.entity_id == order.id
    ).all()
    assert len(audit_records) == 1
    assert audit_records[0].previous_state == "PENDING_PAYMENT"
    assert audit_records[0].new_state == "PAID"

def test_invalid_state_transition_rejected(client, db_session):
    """Test that invalid transition returns 409 with error details."""
    order = OrderFactory(status=OrderStatus.SHIPPED)
    db_session.add(order)
    db_session.commit()
    
    response = client.patch(
        f"/api/v1/orders/{order.id}/state",
        json={"new_state": "PAID"}
    )
    
    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "INVALID_STATE_TRANSITION"
    assert error["details"]["current_state"] == "SHIPPED"
    assert error["details"]["requested_state"] == "PAID"
    assert "DELIVERED" in error["details"]["allowed_transitions"]
```

---

## 11. Docker Compose Configuration

### 10.1 Complete docker-compose.yml

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  db:
    image: postgres:15-alpine
    container_name: articurated_db
    environment:
      POSTGRES_USER: articurated
      POSTGRES_PASSWORD: dev_password
      POSTGRES_DB: articurated_orders
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U articurated"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis (Message Broker + Cache)
  redis:
    image: redis:7-alpine
    container_name: articurated_redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # FastAPI Application
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: articurated_api
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./app:/app/app
      - ./storage:/app/storage
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://articurated:dev_password@db:5432/articurated_orders
      REDIS_URL: redis://redis:6379/0
      ENVIRONMENT: development
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Celery Worker
  worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: articurated_worker
    command: celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2
    volumes:
      - ./app:/app/app
      - ./storage:/app/storage
    environment:
      DATABASE_URL: postgresql://articurated:dev_password@db:5432/articurated_orders
      REDIS_URL: redis://redis:6379/0
      ENVIRONMENT: development
    depends_on:
      - db
      - redis
      - api

  # Celery Beat (Scheduled Tasks)
  beat:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: articurated_beat
    command: celery -A app.tasks.celery_app beat --loglevel=info
    volumes:
      - ./app:/app/app
    environment:
      DATABASE_URL: postgresql://articurated:dev_password@db:5432/articurated_orders
      REDIS_URL: redis://redis:6379/0
      ENVIRONMENT: development
    depends_on:
      - db
      - redis

  # Flower (Celery Monitoring)
  flower:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: articurated_flower
    command: celery -A app.tasks.celery_app flower --port=5555
    ports:
      - "5555:5555"
    environment:
      DATABASE_URL: postgresql://articurated:dev_password@db:5432/articurated_orders
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - redis
      - worker

  # MailHog (Development Email Server)
  mailhog:
    image: mailhog/mailhog:latest
    container_name: articurated_mailhog
    ports:
      - "1025:1025"  # SMTP
      - "8025:8025"  # Web UI
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8025"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
```

### 10.2 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create storage directory
RUN mkdir -p /app/storage/invoices

# Expose port
EXPOSE 8000

# Default command (overridden by docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 10.3 requirements.txt

```
# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9

# Background Jobs
celery==5.3.4
redis==5.0.1
flower==2.0.1

# PDF Generation
weasyprint==60.1

# Email
jinja2==3.1.2

# Storage
boto3==1.29.7  # S3-compatible storage

# Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2
faker==20.1.0
factory-boy==3.3.0

# Monitoring
prometheus-client==0.19.0
structlog==23.2.0
sentry-sdk[fastapi]==1.38.0

# Development
black==23.12.0
ruff==0.1.8
mypy==1.7.1
```

---

## 12. Development Workflow

### 11.1 Initial Setup Commands

```bash
# Clone repository
git clone <repo-url>
cd articurated-order-management

# Copy environment variables
cp .env.example .env

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec api alembic upgrade head

# Verify services
curl http://localhost:8000/api/v1/health
# Open Flower: http://localhost:5555
# Open MailHog: http://localhost:8025
# Open API docs: http://localhost:8000/docs
```

### 11.2 Running Tests

```bash
# Run all tests with coverage
docker-compose exec api pytest

# Run specific test file
docker-compose exec api pytest tests/unit/test_state_machine.py

# Run with verbose output
docker-compose exec api pytest -v

# Generate HTML coverage report
docker-compose exec api pytest --cov-report=html
# View at: htmlcov/index.html
```

### 11.3 Database Management

```bash
# Create new migration
docker-compose exec api alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec api alembic upgrade head

# Rollback migration
docker-compose exec api alembic downgrade -1

# Database shell
docker-compose exec db psql -U articurated -d articurated_orders
```

### 11.4 Monitoring & Debugging

```bash
# View API logs
docker-compose logs -f api

# View worker logs
docker-compose logs -f worker

# Monitor Celery tasks
# Open browser: http://localhost:5555

# View emails (MailHog)
# Open browser: http://localhost:8025

# Execute shell in container
docker-compose exec api bash
```

---

## 13. AI-Assisted Development Guidelines

### 12.1 Optimal Prompting Patterns

**For AI coding assistants (GitHub Copilot, Cursor, etc.):**

✅ **Do:**
- Reference PRD requirements explicitly: "Implement state transition per REQ-001"
- Specify types: "Create Pydantic schema for OrderResponse with all fields from Updated_PRD.md"
- Request tests: "Write pytest for all order state transitions including invalid ones"
- Ask for documentation: "Generate OpenAPI example for this endpoint"

❌ **Don't:**
- Vague requests: "Create order endpoint"
- Skip validation: "Make basic CRUD for orders"
- Ignore audit trail: "Update order status"

### 12.2 Code Generation Templates

**State Machine Implementation:**
```
Prompt: "Implement OrderStatus enum and ORDER_TRANSITIONS dict based on Updated_PRD.md section 4.1. 
Include validation method that checks current_state → new_state is allowed per PRD table."
```

**API Endpoint:**
```
Prompt: "Create FastAPI POST /api/v1/returns endpoint that:
1. Validates order is in DELIVERED state (per REQ-002)
2. Creates return with REQUESTED status
3. Records audit trail entry
4. Returns 201 with ReturnResponse schema
5. Returns 400 if order not DELIVERED with error format from PRD section 4.5"
```

**Background Job:**
```
Prompt: "Create Celery task for invoice generation (REQ-004) with:
- Max 3 retries, exponential backoff
- Generate PDF via WeasyPrint
- Save to storage/invoices/
- Email customer
- Log all steps
- Handle failures gracefully"
```

### 12.3 Testing Prompts

```
Prompt: "Write pytest integration test for complete order lifecycle:
1. Create order (PENDING_PAYMENT)
2. Transition to PAID
3. Transition to PROCESSING_IN_WAREHOUSE
4. Transition to SHIPPED (should trigger invoice job)
5. Transition to DELIVERED
Verify audit trail has 4 entries and invoice task was queued."
```

### 12.4 Type Hints for AI Accuracy

**Always use explicit types:**
```python
# ✅ AI-friendly (explicit types)
def transition_state(
    order_id: UUID,
    new_state: OrderStatus,
    actor_id: UUID | None = None
) -> Order:
    ...

# ❌ AI struggles (no types)
def transition_state(order_id, new_state, actor_id=None):
    ...
```

---

## 14. Success Metrics & Validation

### 13.1 Technical Success Criteria

| Metric | Target | Validation Method |
|--------|--------|-------------------|
| API Response Time (p95) | <200ms | Load testing (k6, locust) |
| Test Coverage | >80% | pytest-cov report |
| State Transition Accuracy | 100% | Integration tests |
| Background Job Success Rate | >99% | Celery task monitoring |
| Zero Invalid State Transitions | 0 errors | Audit trail queries |
| Docker Compose Startup | <30s | Time docker-compose up |

### 13.2 Demo Preparation Checklist

- [ ] All API endpoints implemented and tested
- [ ] State machine validates all transitions per PRD
- [ ] Audit trail records all state changes
- [ ] Invoice generation triggers on SHIPPED
- [ ] Refund processing triggers on COMPLETED
- [ ] Error responses match PRD format
- [ ] Docker Compose starts all services
- [ ] Database migrations run successfully
- [ ] Tests pass with >80% coverage
- [ ] API documentation auto-generated (Swagger)
- [ ] Background job monitoring working (Flower)
- [ ] Email preview working (MailHog)

### 13.3 Demo Script Outline

**8-10 minute demo covering:**

1. **Architecture Overview (2 min)**
   - Show docker-compose.yml services
   - Explain FastAPI + Celery + PostgreSQL stack choices
   - Data flow diagram

2. **API Demonstration (3 min)**
   - Create order via Swagger UI
   - Transition through states (PENDING → PAID → PROCESSING → SHIPPED → DELIVERED)
   - Show invalid transition rejection with error response
   - Query audit trail

3. **Return Workflow (2 min)**
   - Initiate return from DELIVERED order
   - Manager approval
   - Transition through return states
   - Show refund task in Flower

4. **Background Jobs (1 min)**
   - Show invoice generated in storage/invoices/
   - Open MailHog to view invoice email
   - Demonstrate Flower task monitoring

5. **Testing & Code Quality (1 min)**
   - Run pytest with coverage report
   - Show state machine tests (all valid/invalid transitions)
   - Highlight >80% coverage achievement

6. **AI-Assisted Development (1 min)**
   - Show CHAT_HISTORY.md excerpts
   - Explain how AI helped with boilerplate, tests, documentation
   - Highlight key design decisions

---

## 15. Risk Mitigation Strategies

### 14.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| State machine bugs | Medium | Critical | 100% test coverage for all transitions, property-based testing |
| Database deadlocks | Medium | High | Use `with_for_update()` for row locking, optimize transaction scope |
| Celery task failures | Medium | High | Comprehensive retry policies, dead letter queue, alerting |
| Docker networking issues | Low | Medium | Health checks, depends_on conditions, explicit port mappings |
| AI-generated code quality | Medium | Medium | Code reviews, strict type hints, comprehensive tests |

### 14.2 Development Risks (Solo Developer)

| Risk | Mitigation |
|------|------------|
| Scope creep | Strict adherence to PRD requirements, defer "nice-to-haves" |
| Technical debt | AI-assisted refactoring, continuous code quality checks |
| Knowledge gaps | Leverage AI for explanations, maintain CHAT_HISTORY.md |
| Testing blind spots | AI-generate test cases from PRD requirements |
| Documentation lag | Auto-generated API docs, inline docstrings |

---

## 16. Future Enhancement Roadmap

### 15.1 Post-MVP Technical Improvements

**Phase 2 (Performance Optimization):**
- Implement Redis caching for frequent queries
- Add database query optimization (EXPLAIN ANALYZE)
- Introduce connection pooling tuning
- Add CDN for invoice delivery

**Phase 3 (Observability):**
- Integrate Sentry for error tracking
- Add Prometheus + Grafana dashboards
- Implement distributed tracing (OpenTelemetry)
- Set up centralized logging (ELK stack)

**Phase 4 (Scalability):**
- Migrate to Kubernetes (from Docker Compose)
- Implement horizontal pod autoscaling
- Add read replicas for PostgreSQL
- Introduce API rate limiting per customer

**Phase 5 (Advanced Features):**
- GraphQL API option
- WebSocket for real-time order updates
- Event sourcing for audit trail
- CQRS pattern for read/write separation

### 15.2 Out-of-Scope Features (Deferred)

- Customer authentication system (use API keys for now)
- Product catalog management
- Shopping cart functionality
- Multiple warehouse support
- Partial refunds (full refund only in MVP)
- Multi-currency support
- Frontend UI (API-only for MVP)

---

## 17. Appendix

### 16.1 Key File Reference

| File | Purpose | Owner |
|------|---------|-------|
| `Updated_PRD.md` | Business requirements | Product |
| `TECHNICAL_PRD.md` | This document - implementation spec | Engineering |
| `WORKFLOW_DESIGN.md` | State diagrams, DB schema | Engineering |
| `API-SPECIFICATION.yml` | Auto-generated OpenAPI spec | FastAPI |
| `CHAT_HISTORY.md` | AI-assisted development log | Developer |
| `README.md` | Setup & run instructions | Developer |
| `.github/copilot-instructions.md` | AI agent guidance | Developer |

### 16.2 Useful Resources

**FastAPI:**
- Official Docs: https://fastapi.tiangolo.com/
- SQLAlchemy 2.0 Guide: https://docs.sqlalchemy.org/en/20/
- Async Patterns: https://fastapi.tiangolo.com/async/

**Celery:**
- Documentation: https://docs.celeryq.dev/
- Best Practices: https://docs.celeryq.dev/en/stable/userguide/tasks.html#best-practices
- Flower Monitoring: https://flower.readthedocs.io/

**Testing:**
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
- Factory Boy: https://factoryboy.readthedocs.io/
- Coverage.py: https://coverage.readthedocs.io/

**Docker:**
- Compose Docs: https://docs.docker.com/compose/
- Multi-stage Builds: https://docs.docker.com/build/building/multi-stage/

### 16.3 Environment Variables Reference

```bash
# .env.example

# Database
DATABASE_URL=postgresql://articurated:dev_password@localhost:5432/articurated_orders

# Redis
REDIS_URL=redis://localhost:6379/0

# Environment
ENVIRONMENT=development  # development | testing | production

# Security
SECRET_KEY=your-secret-key-here-change-in-production
API_KEY=dev-api-key

# Email (Development)
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=

# Email (Production)
# SMTP_HOST=smtp.sendgrid.net
# SMTP_PORT=587
# SMTP_USER=apikey
# SMTP_PASSWORD=your-sendgrid-api-key

# Storage (Development)
STORAGE_TYPE=local
STORAGE_PATH=/app/storage

# Storage (Production)
# STORAGE_TYPE=s3
# AWS_ACCESS_KEY_ID=your-access-key
# AWS_SECRET_ACCESS_KEY=your-secret-key
# AWS_S3_BUCKET=articurated-invoices
# AWS_REGION=us-east-1

# Monitoring (Optional)
# SENTRY_DSN=https://your-sentry-dsn
# PROMETHEUS_PORT=9090
```

---

## 18. Conclusion

This technical PRD provides a comprehensive implementation roadmap for the ArtiCurated Order Management System using a Python-based stack optimized for AI-assisted solo development. 

**Key Technical Decisions Summary:**
- **FastAPI**: Performance, auto-docs, type safety
- **PostgreSQL**: ACID compliance, JSON support, mature
- **Celery + Redis**: Battle-tested background jobs, monitoring
- **SQLAlchemy 2.0**: Modern ORM with type hints
- **Docker Compose**: Simple deployment, reproducible environment

**Success Factors:**
1. Strict adherence to PRD state machine requirements
2. Comprehensive testing (>80% coverage)
3. Immutable audit trail for compliance
4. AI-friendly type hints and documentation
5. Background job reliability with retries

**Next Steps:**
1. Initialize project structure
2. Set up Docker Compose environment
3. Implement database schema with migrations
4. Build state machine with 100% test coverage
5. Create API endpoints with validation
6. Implement background jobs with monitoring
7. Prepare demo and documentation

---

**Document Approval:**

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Lead Technical Engineer | [Your Name] | Dec 2024 | ✓ |
| Product Manager | [PM Name] | TBD | |

**Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Dec 2024 | Lead Engineer | Initial technical specification |

---

**End of Technical PRD**
