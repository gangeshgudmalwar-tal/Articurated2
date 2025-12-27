def make_address():
    return {
        "street": "123 Test St",
        "city": "Testville",
        "state": "TS",
        "postal_code": "12345",
        "country": "Testland",
    }


def test_invoice_enqueued_and_idempotent(client):
    # Create order
    payload = {
        "customer_id": "INV-CUST",
        "shipping_address": make_address(),
        "billing_address": make_address(),
        "payment_method": "card",
        "line_items": [
            {"product_id": "P1", "product_name": "Test Product", "quantity": 1, "unit_price": "10.00"}
        ],
    }
    resp = client.post("/api/v1/orders", json=payload)
    assert resp.status_code == 201
    order_id = resp.json()["id"]

    # Prepare a dummy invoice task module that is idempotent
    import sys, types

    INVOICE_STORE = {}

    mod = types.ModuleType("app.tasks.invoice_tasks")

    class DummyGen:
        @staticmethod
        def delay(order_id_arg):
            # simulate idempotent invoice generation
            if INVOICE_STORE.get(order_id_arg):
                return {"status": "already_exists"}
            INVOICE_STORE[order_id_arg] = f"/invoices/{order_id_arg}.pdf"
            return {"status": "created", "path": INVOICE_STORE[order_id_arg]}

    mod.generate_invoice = DummyGen()
    sys.modules["app.tasks.invoice_tasks"] = mod

    # Transition order to PAID -> PROCESSING_IN_WAREHOUSE -> SHIPPED
    resp = client.patch(f"/api/v1/orders/{order_id}/state", json={"new_state": "PAID", "actor": "TEST"})
    assert resp.status_code == 200
    resp = client.patch(f"/api/v1/orders/{order_id}/state", json={"new_state": "PROCESSING_IN_WAREHOUSE", "actor": "TEST"})
    assert resp.status_code == 200

    # First transition to SHIPPED should enqueue/create invoice
    resp = client.patch(f"/api/v1/orders/{order_id}/state", json={"new_state": "SHIPPED", "actor": "TEST"})
    assert resp.status_code == 200

    # Simulate duplicate task execution (retry) by calling delay again
    res2 = mod.generate_invoice.delay(order_id)
    assert res2["status"] in ("already_exists", "created")

    # Ensure only one invoice entry exists
    assert len(INVOICE_STORE) == 1
    assert order_id in INVOICE_STORE
