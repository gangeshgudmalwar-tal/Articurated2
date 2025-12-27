# ArtiCurated Order Management System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A robust backend system for managing order lifecycle and returns in the ArtiCurated boutique marketplace.

## Features

- ✅ **Deterministic State Machines** - Order and return lifecycle management with validation
- ✅ **Audit Trail** - Complete immutable history of all state transitions
- ✅ **Background Processing** - Async invoice generation and refund processing via Celery
- ✅ **API-First Design** - RESTful API with auto-generated OpenAPI documentation
- ✅ **Type-Safe** - Full type hints for better IDE support and AI-assisted development
- ✅ **Comprehensive Testing** - >80% code coverage with unit, integration, and E2E tests

## Tech Stack

- **Framework:** FastAPI 0.104 (async-capable, high performance)
- **Database:** PostgreSQL 15 (ACID compliance, JSONB support)
- **ORM:** SQLAlchemy 2.0 (modern, type-safe)
- **Background Jobs:** Celery 5.3 + Redis 7
- **PDF Generation:** WeasyPrint
- **Testing:** pytest + pytest-asyncio
- **Deployment:** Docker Compose

## Quick Start

### Prerequisites

- Docker Desktop or Docker Engine 20+
- Docker Compose 2.0+
- 4GB RAM minimum

### Setup & Run

```bash
# Clone repository
git clone <repository-url>
cd assignment2

# Copy environment variables
cp .env.example .env

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec api alembic upgrade head

# Verify services are running
curl http://localhost:8000/api/v1/health
```

### Access Services

| Service | URL | Description |
|---------|-----|-------------|
| **API Documentation** | http://localhost:8000/docs | Swagger UI with interactive API testing |
| **API (Alternative)** | http://localhost:8000/redoc | ReDoc API documentation |
| **Flower** | http://localhost:5555 | Celery task monitoring dashboard |
| **MailHog** | http://localhost:8025 | Email testing interface |
| **PostgreSQL** | localhost:5432 | Database (credentials in .env) |

## Project Structure

```
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── config.py                  # Configuration management
│   ├── database.py                # Database session management
│   ├── api/v1/                    # API routes
│   │   ├── orders.py
│   │   ├── returns.py
│   │   └── health.py
│   ├── models/                    # SQLAlchemy models
│   │   ├── order.py
│   │   ├── return_request.py
│   │   └── state_history.py
│   ├── schemas/                   # Pydantic request/response models
│   ├── services/                  # Business logic
│   │   ├── state_machine.py      # State transition validation
│   │   ├── order_service.py
│   │   └── return_service.py
│   ├── tasks/                     # Celery background jobs
│   │   ├── invoice_tasks.py
│   │   └── refund_tasks.py
│   └── utils/                     # Utilities
├── tests/                         # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── alembic/                       # Database migrations
├── storage/                       # Local blob storage (dev)
├── templates/                     # Email & PDF templates
└── docker-compose.yml             # Docker services definition
```

## Development

### Running Tests

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

### Database Management

```bash
# Create new migration
docker-compose exec api alembic revision --autogenerate -m "Add column description"

# Apply migrations
docker-compose exec api alembic upgrade head

# Rollback migration
docker-compose exec api alembic downgrade -1

# Database shell
docker-compose exec db psql -U articurated -d articurated_orders
```

### Monitoring & Debugging

```bash
# View API logs
docker-compose logs -f api

# View worker logs
docker-compose logs -f worker

# Monitor Celery tasks
# Open browser: http://localhost:5555

# View sent emails (development)
# Open browser: http://localhost:8025

# Execute shell in container
docker-compose exec api bash
```

### Code Quality

```bash
# Format code with Black
docker-compose exec api black app tests

# Lint with Ruff
docker-compose exec api ruff check app tests

# Type check with mypy
docker-compose exec api mypy app
```

## API Usage Examples

### Create Order

```bash
curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key" \
  -d '{
    "customer_id": "550e8400-e29b-41d4-a716-446655440000",
    "line_items": [
      {
        "product_id": "650e8400-e29b-41d4-a716-446655440001",
        "product_name": "Handcrafted Ceramic Vase",
        "quantity": 1,
        "unit_price": 129.99
      }
    ],
    "shipping_address": {
      "street": "123 Main St",
      "city": "San Francisco",
      "state": "CA",
      "zip": "94102",
      "country": "USA"
    },
    "billing_address": {
      "street": "123 Main St",
      "city": "San Francisco",
      "state": "CA",
      "zip": "94102",
      "country": "USA"
    },
    "payment_method": "credit_card"
  }'
```

### Transition Order State

```bash
curl -X PATCH "http://localhost:8000/api/v1/orders/{order_id}/state" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key" \
  -d '{
    "new_state": "PAID",
    "reason": "Payment confirmed via Stripe"
  }'
```

### Initiate Return

```bash
curl -X POST "http://localhost:8000/api/v1/returns" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key" \
  -d '{
    "order_id": "550e8400-e29b-41d4-a716-446655440000",
    "reason": "Item damaged during shipping",
    "customer_notes": "Box was crushed, visible cracks on vase"
  }'
```

## State Machine Rules

### Order States

```
PENDING_PAYMENT → PAID → PROCESSING_IN_WAREHOUSE → SHIPPED → DELIVERED
      ↓            ↓
  CANCELLED   CANCELLED
```

**Allowed Transitions:**
- `PENDING_PAYMENT` → `PAID` or `CANCELLED`
- `PAID` → `PROCESSING_IN_WAREHOUSE` or `CANCELLED`
- `PROCESSING_IN_WAREHOUSE` → `SHIPPED`
- `SHIPPED` → `DELIVERED` (triggers invoice generation)

### Return States

```
REQUESTED → APPROVED → IN_TRANSIT → RECEIVED → COMPLETED
     ↓
  REJECTED
```

**Allowed Transitions:**
- `REQUESTED` → `APPROVED` or `REJECTED`
- `APPROVED` → `IN_TRANSIT`
- `IN_TRANSIT` → `RECEIVED`
- `RECEIVED` → `COMPLETED` (triggers refund processing)

## Documentation

- **[Updated_PRD.md](Updated_PRD.md)** - Business requirements and specifications
- **[TECHNICAL_PRD.md](TECHNICAL_PRD.md)** - Technical implementation details
- **[WORKFLOW_DESIGN.md](WORKFLOW_DESIGN.md)** - State diagrams and database schema
- **[API-SPECIFICATION.yml](API-SPECIFICATION.yml)** - OpenAPI 3.0 specification
- **[CHAT_HISTORY.md](CHAT_HISTORY.md)** - AI-assisted development decisions
- **[.github/copilot-instructions.md](.github/copilot-instructions.md)** - AI agent guidance

## Architecture

### Request Flow

```
Client → FastAPI → Service Layer → State Machine Validation
                       ↓
                  Database Transaction:
                    - Update State
                    - Insert Audit Record
                       ↓
                  Background Job (if needed)
                       ↓
                  Response to Client
```

### Background Jobs

**Invoice Generation (on SHIPPED):**
- Generate PDF via WeasyPrint
- Store in blob storage
- Email customer with attachment
- Retry: 3x with exponential backoff

**Refund Processing (on COMPLETED):**
- Call payment gateway API
- Store transaction ID
- Email customer confirmation
- Retry: 5x with exponential backoff
- Alert on final failure

## Performance

- **API Response Time:** <200ms (p95) for read operations
- **API Response Time:** <500ms (p95) for write operations
- **Background Job Pickup:** <30 seconds
- **Database Queries:** Optimized with indexes, <50ms (p95)

## Security

- ✅ API Key authentication (development) / JWT (production)
- ✅ SQL injection prevention via parameterized queries
- ✅ Row-level locking for concurrent state transitions
- ✅ HTTPS/TLS 1.3 (production)
- ✅ Rate limiting (100 requests/minute per client)

## Contributing

1. Create feature branch: `git checkout -b feature/amazing-feature`
2. Write tests for new functionality
3. Ensure tests pass: `pytest --cov`
4. Format code: `black app tests`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push branch: `git push origin feature/amazing-feature`
7. Open Pull Request

## Troubleshooting

### Common Issues

**Services fail to start:**
```bash
# Check logs
docker-compose logs

# Restart services
docker-compose down
docker-compose up -d
```

**Database connection errors:**
```bash
# Check if database is healthy
docker-compose ps
# Wait for health check to pass
```

**Migrations fail:**
```bash
# Reset database (CAUTION: Destroys all data)
docker-compose down -v
docker-compose up -d
docker-compose exec api alembic upgrade head
```

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
- Create an issue in the repository
- Contact: engineering@articurated.com

---

**Built with ❤️ using FastAPI, PostgreSQL, and AI-assisted development tools**
