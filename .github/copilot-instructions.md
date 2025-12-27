# AI Agent Instructions - ArtiCurated Order Management

## 🎯 Quick Reference

**Framework:** v2.0 Production | **Budget:** 150 PRU/PR | **Cost:** $0.01-$0.02/PR

### Load Strategy

| Task Type | Files to Load | PRU | Cost | Example |
|-----------|---------------|-----|------|---------|
| **Feature** | orchestrator + analysis + implementation | 100 | $0.010 | "Add partial refund API" |
| **Bug Fix** | orchestrator + implementation + validation | 80 | $0.008 | "Fix refund calculation error" |
| **Security** | validation only (FREE tools: bandit, safety) | 0 | $0.000 | "Scan for vulnerabilities" |
| **Deploy** | deployment only (Docker + GitHub Actions) | 30 | $0.003 | "Deploy to staging" |

**Navigation:**
- 📋 [agents.md](agents.md) - Agent definitions (5 agents, 200 lines)
- 📋 [skills.md](skills.md) - Skill library (26+ skills, 200 lines)
- 📁 [agents/](agents/) - Detailed agent YAML files
- 📁 [skills/](skills/) - Detailed skill YAML files

---

## 💡 Concrete Examples

### Example 1: Add New API Endpoint

**Request:** "Add GET /api/v1/orders/{id}/audit endpoint"

**Context to load:**
```yaml
1. agents/orchestrator.yml        # 150 lines, routing
2. agents/analysis.yml            # 180 lines, API design
3. agents/implementation.yml      # 200 lines, code gen
4. skills/architecture/design_api.yml  # 140 lines
5. skills/development/generate_code.yml  # 130 lines
Total: 800 lines, 75 PRU, $0.008, ~6 minutes
```

**Workflow:**
1. Design endpoint (follows existing pattern in API-SPECIFICATION.yml)
2. Generate FastAPI route with Pydantic schema
3. Implement service method to query StateHistory model
4. Write pytest tests (parametrized for coverage)
5. Update OpenAPI spec
6. Auto-deploy if tests pass

**Copilot command:**
```bash
@workspace /explain Add audit trail endpoint to orders API
# Copilot uses existing patterns from app/api/v1/orders.py
```

### Example 2: Fix State Transition Bug

**Request:** "Can't transition order from SHIPPED to CANCELLED"

**Context to load:**
```yaml
1. agents/orchestrator.yml        # 150 lines
2. agents/implementation.yml      # 200 lines
3. app/services/state_machine.py  # 150 lines (contains ORDER_TRANSITIONS)
Total: 500 lines, 60 PRU, $0.006, ~3 minutes
```

**Workflow:**
1. Check ORDER_TRANSITIONS dict in state_machine.py
2. Update allowed transitions for SHIPPED state
3. Add test case for new transition
4. Run pytest to verify
5. Fast-track deployment (no gate needed for bug fix)

**Copilot command:**
```bash
@workspace /fix state machine transitions in app/services/state_machine.py
# Copilot identifies missing transition in ORDER_TRANSITIONS dict
```

### Example 3: Run Security Scan

**Request:** "Check for SQL injection vulnerabilities"

**Context to load:**
```yaml
1. agents/validation.yml          # 180 lines
2. skills/security/*.yml          # 300 lines (all FREE tools)
Total: 480 lines, 0 PRU, $0.000 (all FREE), ~2 minutes
```

**Workflow:**
1. Run bandit (FREE Python security linter)
2. Run safety (FREE dependency checker)
3. Check SQLAlchemy patterns (ORM prevents SQL injection)
4. Report findings (0 issues expected if using ORM)

**Command:**
```bash
# Automated in GitHub Actions
pytest tests/security/  # FREE
bandit -r app/          # FREE
safety check            # FREE
```

---

## 🏗️ System Architecture (ArtiCurated Order Management)

**One Sentence:** Stateless FastAPI service with deterministic state machines, immutable audit trail, and async background jobs.

### Core Components

```
Client Request
    ↓
FastAPI API (/api/v1/orders, /api/v1/returns)
    ↓
Service Layer (order_service.py, return_service.py)
    ↓
State Machine (ORDER_TRANSITIONS, RETURN_TRANSITIONS dicts)
    ↓
Database (PostgreSQL: orders, returns, state_history)
    ↓
Celery Jobs (invoices on SHIPPED, refunds on COMPLETED)
```

### State Machines (Immutable Rules)

**Order States:**
```python
PENDING_PAYMENT → PAID → PROCESSING_IN_WAREHOUSE → SHIPPED → DELIVERED
                   ↓                                              ↑
                CANCELLED ←──────────────────────────────────────┘
```

**Return States:**
```python
REQUESTED → APPROVED → IN_TRANSIT → RECEIVED → COMPLETED
         ↓
      REJECTED
```

**Critical:** All transitions validated by `app/services/state_machine.py` using ORDER_TRANSITIONS and RETURN_TRANSITIONS dictionaries.

### API Example (Follow This Pattern)

```python
# POST /api/v1/orders
{
  "customer_id": "CUST-001",
  "items": [{"sku": "ITEM-001", "quantity": 2, "price": 29.99}],
  "shipping_address": {"street": "123 Main St", ...}
}
→ Response: 201 Created, order.status = "PENDING_PAYMENT"

# PATCH /api/v1/orders/:id/state
{"new_state": "PAID"}
→ Validates transition, updates DB, creates audit record
→ Response: 200 OK, order.status = "PAID"

# Invalid transition example:
{"new_state": "SHIPPED"}  # from PENDING_PAYMENT
→ Response: 400 Bad Request
{
  "error": {
    "code": "INVALID_STATE_TRANSITION",
    "message": "Cannot transition from PENDING_PAYMENT to SHIPPED",
    "details": {
      "current_state": "PENDING_PAYMENT",
      "requested_state": "SHIPPED",
      "allowed_transitions": ["PAID", "CANCELLED"]
    }
  }
}
```

### Project Structure (Where to Edit)

```
app/
├── main.py                    # FastAPI app initialization
├── api/v1/
│   ├── orders.py              # Order CRUD + state transitions
│   ├── returns.py             # Return workflow endpoints
│   └── health.py              # Health check
├── models/                    # SQLAlchemy models
│   ├── order.py               # Order + OrderLineItem tables
│   ├── return_request.py      # Return entity
│   └── state_history.py       # Audit trail (IMMUTABLE)
├── services/
│   ├── state_machine.py       # ⭐ STATE TRANSITION VALIDATION
│   ├── order_service.py       # Order business logic
│   ├── return_service.py      # Return business logic
│   └── audit_service.py       # Audit record creation
├── tasks/                     # Celery background jobs
│   ├── invoice_tasks.py       # Generate PDF on SHIPPED
│   └── refund_tasks.py        # Process refund on COMPLETED
└── utils/
    ├── invoice_generator.py   # WeasyPrint PDF generation
    └── email_sender.py        # SMTP email notifications
```

---

## ✅ Development Workflow (TDD Required)

**Principle:** Test first, then implement. 85% coverage minimum.

### Workflow Steps

1. **Write failing test** (captures requirement)
```python
def test_transition_to_paid():
    order = create_order(status="PENDING_PAYMENT")
    result = order_service.transition_state(order, "PAID")
    assert result.status == "PAID"
```

2. **Implement minimal code** (makes test pass)
```python
def transition_state(self, order, new_state):
    if not StateMachine.validate_transition(order.status, new_state):
        raise ValueError("Invalid transition")
    order.status = new_state
    self.db.commit()
    return order
```

3. **Refactor** (improve quality, tests still pass)
4. **Verify coverage** (`pytest --cov=app` → must be ≥85%)
5. **Integrate** (GitHub Actions runs all tests automatically)

**Reference:** Full TDD framework in [`docs/TDD_FRAMEWORK.md`](docs/TDD_FRAMEWORK.md)

---

## 🔧 Coding Standards

**Type hints everywhere:**
```python
def create_order(self, order_data: OrderCreate) -> Order:
    """Create new order with PENDING_PAYMENT status."""
```

**Pydantic for validation:**
```python
class OrderCreate(BaseModel):
    customer_id: str = Field(..., min_length=1)
    items: List[OrderItem] = Field(..., min_items=1)
```

**Data-driven state validation:**
```python
# ✅ Good (testable, clear)
ORDER_TRANSITIONS = {
    OrderStatus.PENDING_PAYMENT: {OrderStatus.PAID, OrderStatus.CANCELLED},
    OrderStatus.PAID: {OrderStatus.PROCESSING_IN_WAREHOUSE, OrderStatus.CANCELLED},
    ...
}

# ❌ Bad (hard to test, opaque)
if order.status == "PENDING_PAYMENT" and new_status == "PAID":
    order.status = new_status
elif order.status == "PAID" and new_status == "PROCESSING_IN_WAREHOUSE":
    ...
```

**Idempotent background jobs:**
```python
@celery_app.task(bind=True, max_retries=3)
def generate_invoice(self, order_id):
    # Check if already done
    if invoice_exists(order_id):
        return {"status": "already_exists"}
    
    # Generate invoice
    pdf = create_pdf(order_id)
    store_pdf(pdf)
    send_email(order_id, pdf_url)
```

---

## 📚 Documentation References

| Document | Purpose | When to Read |
|----------|---------|--------------|
| [Updated_PRD.md](../Updated_PRD.md) | Business requirements, state machines | Understanding domain rules |
| [TECHNICAL_PRD.md](../TECHNICAL_PRD.md) | Tech stack, architecture, TDD | Implementation guidance |
| [API-SPECIFICATION.yml](../API-SPECIFICATION.yml) | API contracts (OpenAPI) | Designing/implementing APIs |
| [WORKFLOW_DESIGN.md](../WORKFLOW_DESIGN.md) | State diagrams, DB schema | Understanding workflows |
| [docs/TDD_FRAMEWORK.md](docs/TDD_FRAMEWORK.md) | Testing strategy | Writing tests |
| [docs/MCP_ASSIGNMENT_MATRIX.md](docs/MCP_ASSIGNMENT_MATRIX.md) | MCP server integration | Advanced optimization |

---

## 🚀 Quick Commands

```bash
# Run tests
pytest --cov=app --cov-report=html  # All tests + coverage
pytest tests/unit/                  # Unit tests only
pytest -k "state_machine"           # Specific tests

# Security scans (FREE)
bandit -r app/
safety check
pytest tests/security/

# Run locally
docker-compose up  # Starts all services
# API: http://localhost:8000
# Swagger docs: http://localhost:8000/docs

# Deploy
git push origin main  # Triggers GitHub Actions
```

---

## 💡 Best Practices for AI Agents

- **Type hints everywhere:** AI tools generate 40% more accurate code with full type annotations (see CHAT_HISTORY.md Section 12).
- **Use explicit Pydantic schemas:** FastAPI auto-validates requests and generates OpenAPI docs.
- **Parametrized tests for state machines:** Use `@pytest.mark.parametrize` to test all transition combinations efficiently.
- **Data-driven validation:** Store allowed transitions in dictionaries (`ORDER_TRANSITIONS`), not if/else chains—easier to test and visualize.
- **Idempotent background jobs:** Always check if work already done (e.g., invoice exists?) before processing.
- **Error format consistency:** Return `{"error": {"code": "...", "message": "...", "details": {...}}}` per API-SPECIFICATION.yml.

### Quick Reference
- Run tests: `docker-compose exec api pytest --cov`
- API docs (Swagger): http://localhost:8000/docs
- Celery monitoring (Flower): http://localhost:5555
- Email preview (MailHog): http://localhost:8025
- Database migrations: `docker-compose exec api alembic revision --autogenerate -m "description"`

### AI Tooling & MCP Context (Authoritative)

- GitHub MCP: Use as the source of truth for repository structure, diffs, and existing patterns.
- OpenAPI MCP: Treat API-SPECIFICATION.yml as authoritative. Do not invent endpoints or schemas.
- Database MCP: Use for validating indexes, migrations, and query patterns (especially StateHistory).
- Testing MCP: Generate tests first for state transitions and background jobs.
- Docker MCP: Validate docker-compose.yml, healthchecks, and service wiring.

### Agent Operating Mode (Strict)

- You must reject convenience shortcuts that violate the PRD.
- You must prefer correctness over brevity.
- You must fail fast on invalid state transitions.
- You must never silently ignore errors.
- Write tests before implementation.
- Cover all valid transitions.
- Explicitly test forbidden transitions.
- Prefer parametrized tests.
- Background jobs must be idempotent.
- Always check if work is already done.
- Follow defined retry limits and backoff.
- Log failures with context.
- Follow existing project structure.
- Reuse patterns before introducing new ones.
- Do not duplicate logic.

### Next Steps for Coding Agent
- If code is added: locate API entrypoints, find or add a central state-transition module, add audit writes on every transition, and wire background job triggers for SHIPPED and COMPLETED.

---

**Framework Version:** v3.0 Governance-First  
**Last Updated:** December 2025  
**Budget:** 100 PRU Hard Limit | Default: 0 PRU (Copilot + Static Tools)

---

## 🤖 AI Orchestration Alignment

**Core Principle:** Minimize hallucinations, prevent complexity, respect cost constraints.

### Rules Copilot Must Follow

**Code Generation:**
- **Prefer existing patterns:** Match style/structure from codebase before inventing new approaches
- **Pythonic and simple:** Clarity over cleverness, explicit over implicit
- **Type hints everywhere:** Full annotations on all functions/methods (enables better validation)
- **Minimal dependencies:** Use stdlib first, avoid unnecessary 3rd-party libs
- **Testable by default:** Write code that's easy to test, avoid coupling

**Architecture Decisions:**
- **Never change architecture without approval:** Flag breaking changes, don't implement them
- **If logic becomes complex:** Suggest running Logic Validator CLI (`make validate-logic`)
- **State machine changes:** ALWAYS require validation (critical business logic)
- **No implicit coupling:** Avoid hidden dependencies between modules

**Cost Awareness:**
- **Default to 0 PRU:** Use Copilot + static tools (pytest, bandit, ruff, mypy) whenever possible
- **Escalate when justified:** Only suggest AI validation for HIGH risk (state machines, security, payments)
- **Track PRU usage:** When AI used, log with `make track-pru AGENT=... MODEL=... PRU=... CONTEXT='...'`

**Testing:**
- **TDD required:** Write tests before implementation, 85% coverage minimum
- **Avoid excessive scaffolding:** Generate focused tests, not boilerplate
- **Parametrized tests:** Use `@pytest.mark.parametrize` for state transitions
- **Security tests:** Use `make gen-adversarial TARGET=...` for security-critical code

**Workflow Integration:**
- **Check scope first:** Run `make validate-scope FILES='...' LINES=N` before starting work
- **Validate logic:** Run `make validate-logic FILES='...' RISK=MEDIUM` for business logic changes
- **Track costs:** Use `make track-pru` to log PRU usage
- **Check budget:** Run `make report PERIOD=today` to monitor budget status

### When Uncertain

**Ask clarifying questions:**
- "This change affects state transitions. Should I run Logic Validator first?"
- "This adds a new dependency. Is it necessary or can we use stdlib?"
- "This increases complexity. Should we refactor existing code instead?"

**Don't:**
- Guess at requirements or make assumptions
- Generate code without understanding the PRD/spec
- Add features not explicitly requested
- Change architecture without discussion

### Tone & Communication

**Direct, calm, engineering-focused:**
- State facts, not opinions
- Suggest validation when needed, don't block autonomously
- Explain trade-offs clearly
- Keep responses concise and actionable

### Examples

**✅ Good:**
```python
# Copilot generates code matching existing pattern
def transition_state(self, order: Order, new_state: OrderStatus) -> Order:
    """Transition order to new state with validation."""
    if not StateMachine.validate_transition(order.status, new_state):
        raise InvalidStateTransitionError(order.status, new_state)
    # ... existing pattern from state_machine.py
```

**❌ Bad:**
```python
# Copilot invents new pattern without checking existing code
def change_order_status(order, status):  # Missing type hints
    order.status = status  # No validation!
    return order
```

**✅ Good Response:**
"This change modifies ORDER_TRANSITIONS in state_machine.py. I suggest running `make validate-logic FILES='app/services/state_machine.py' RISK=HIGH` to validate all transition paths before merging."

**❌ Bad Response:**
"I've updated the state machine. It should work fine, but you might want to test it."

### Cost Budget Tracking

**Session Budget:** 100 PRU  
**Alert Threshold:** 75 PRU (75%)

**Check budget status:**
```bash
make report PERIOD=session
```

**If approaching limit:**
- Switch to static tools only (pytest, bandit, ruff)
- Defer AI validation to next session
- Notify team lead if critical validation blocked

---

## Legacy Information (v2.0 Archived)

For detailed specifications, see:
- [agents/](agents/) - v3.0 agent definitions (governance-first)
- [skills_v3.yml](skills_v3.yml) - Complete skill library
- [cli/](../cli/) - Local CLI utilities (scope, logic, adversarial, pru_tracker)
