# User Stories

## Story 001 - Order audit endpoint
As a developer or auditor,
I want a GET /api/v1/orders/{order_id}/audit endpoint,
So that I can retrieve the immutable state history/audit trail for an order.

Acceptance criteria:
- GET /api/v1/orders/{order_id}/audit returns 200 with JSON {"history": [...]} for existing orders
- Each entry in history contains timestamp, previous_state, new_state, changed_by
- Returns 404 for unknown order_id

---

## Story 002 - Order state transition API
As an operator,
I want PATCH /api/v1/orders/{order_id}/state to change order state,
So that state transitions are validated by the state machine and recorded in audit.

Acceptance criteria:
- Valid transitions return 200 and append to audit trail
- Invalid transitions return 400 with structured error code INVALID_STATE_TRANSITION

---

## Story 003 - Trigger invoice on SHIPPED
As the billing system,
When order transitions to SHIPPED,
An invoice generation task should be scheduled (idempotent) and invoice URL stored.

Acceptance criteria:
- Transition to SHIPPED enqueues invoice task
- Repeated transitions or retries do not create duplicate invoices

