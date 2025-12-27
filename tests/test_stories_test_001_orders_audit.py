

def make_address():
    return {
        "street": "123 Test St",
        "city": "Testville",
        "state": "TS",
        "postal_code": "12345",
        "country": "Testland",
    }


def test_create_order_and_get_audit_trail(client):
    order_payload = {
        "customer_id": "TEST-CUST",
        "shipping_address": make_address(),
        "billing_address": make_address(),
        "payment_method": "card",
        "line_items": [
            {"product_id": "P1", "product_name": "Test Product", "quantity": 1, "unit_price": "10.00"}
        ],
    }
    resp = client.post("/api/v1/orders", json=order_payload)
    assert resp.status_code == 201
    order = resp.json()
    order_id = order["id"]

    resp = client.get(f"/api/v1/orders/{order_id}/audit")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, dict)
    assert "history" in body
    assert isinstance(body["history"], list)
    assert len(body["history"]) >= 1
    # initial state should be recorded
    assert body["history"][0]["new_state"] == "PENDING_PAYMENT"
