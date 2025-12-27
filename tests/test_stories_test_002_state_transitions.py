def make_address():
    return {
        "street": "123 Test St",
        "city": "Testville",
        "state": "TS",
        "postal_code": "12345",
        "country": "Testland",
    }


def create_order(client):
    payload = {
        "customer_id": "TRANS-CUST",
        "shipping_address": make_address(),
        "billing_address": make_address(),
        "payment_method": "card",
        "line_items": [
            {"product_id": "P1", "product_name": "Test Product", "quantity": 1, "unit_price": "10.00"}
        ],
    }
    resp = client.post("/api/v1/orders", json=payload)
    assert resp.status_code == 201
    return resp.json()["id"]


def test_invalid_then_valid_transitions_and_invoice_enqueued(client, monkeypatch):
    order_id = create_order(client)

    # Invalid transition: PENDING_PAYMENT -> SHIPPED should be rejected
    resp = client.patch(f"/api/v1/orders/{order_id}/state", json={"new_state": "SHIPPED", "actor": "TEST"})
    assert resp.status_code == 400
    err = resp.json()
    assert "error" in err
    assert err["error"]["code"] == "INVALID_STATE_TRANSITION"
    assert "allowed_transitions" in err["error"]["details"]

    # Valid transitions
    resp = client.patch(f"/api/v1/orders/{order_id}/state", json={"new_state": "PAID", "actor": "TEST"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "PAID"

    resp = client.patch(f"/api/v1/orders/{order_id}/state", json={"new_state": "PROCESSING_IN_WAREHOUSE", "actor": "TEST"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "PROCESSING_IN_WAREHOUSE"

    # Inject a dummy invoice_tasks module to avoid importing celery in tests
    import sys, types
    called = []

    mod = types.ModuleType("app.tasks.invoice_tasks")

    class DummyGen:
        @staticmethod
        def delay(arg):
            called.append(arg)

    mod.generate_invoice = DummyGen()
    sys.modules["app.tasks.invoice_tasks"] = mod

    resp = client.patch(f"/api/v1/orders/{order_id}/state", json={"new_state": "SHIPPED", "actor": "TEST"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "SHIPPED"

    # ensure invoice task was enqueued (delay called)
    assert called == [order_id]

    # audit trail contains SHIPPED
    resp = client.get(f"/api/v1/orders/{order_id}/audit")
    assert resp.status_code == 200
    history = resp.json()["history"]
    assert any(h["new_state"] == "SHIPPED" for h in history)
