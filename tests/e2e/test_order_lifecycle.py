"""
End-to-end test for complete order lifecycle.
"""
import pytest
from app.services.state_machine import OrderStatus


class TestOrderLifecycle:
    """Test complete order workflow from creation to delivery."""

    def test_complete_order_lifecycle(self, client, sample_order_data):
        """
        Test the complete order lifecycle:
        1. Create order (PENDING_PAYMENT)
        2. Process payment (PAID)
        3. Warehouse processing (PROCESSING_IN_WAREHOUSE)
        4. Ship order (SHIPPED)
        5. Deliver order (DELIVERED)
        """
        # Step 1: Create order
        response = client.post("/api/v1/orders", json=sample_order_data)
        assert response.status_code == 201
        order = response.json()
        assert order["status"] == OrderStatus.PENDING_PAYMENT
        order_id = order["id"]

        # Step 2: Process payment
        response = client.patch(
            f"/api/v1/orders/{order_id}/state",
            json={
                "new_state": OrderStatus.PAID,
                "actor": sample_order_data["customer_id"],
                "notes": "Payment processed via credit card",
            }
        )
        assert response.status_code == 200
        assert response.json()["status"] == OrderStatus.PAID

        # Step 3: Warehouse processing
        response = client.patch(
            f"/api/v1/orders/{order_id}/state",
            json={
                "new_state": OrderStatus.PROCESSING_IN_WAREHOUSE,
                "actor": "SYSTEM",
                "trigger": "BACKGROUND_JOB",
                "notes": "Order picked and packed",
            }
        )
        assert response.status_code == 200
        assert response.json()["status"] == OrderStatus.PROCESSING_IN_WAREHOUSE

        # Step 4: Ship order
        response = client.patch(
            f"/api/v1/orders/{order_id}/state",
            json={
                "new_state": OrderStatus.SHIPPED,
                "actor": "SYSTEM",
                "trigger": "WEBHOOK",
                "notes": "Shipped via FedEx",
            }
        )
        assert response.status_code == 200
        order = response.json()
        assert order["status"] == OrderStatus.SHIPPED

        # Update shipping info
        response = client.patch(
            f"/api/v1/orders/{order_id}/shipping",
            json={
                "tracking_number": "1Z999AA10123456784",
                "carrier": "FedEx",
            }
        )
        assert response.status_code == 200
        assert response.json()["tracking_number"] == "1Z999AA10123456784"

        # Step 5: Deliver order
        response = client.patch(
            f"/api/v1/orders/{order_id}/state",
            json={
                "new_state": OrderStatus.DELIVERED,
                "actor": "SYSTEM",
                "trigger": "WEBHOOK",
                "notes": "Delivered and signed for",
            }
        )
        assert response.status_code == 200
        assert response.json()["status"] == OrderStatus.DELIVERED

        # Verify audit trail
        response = client.get(f"/api/v1/orders/{order_id}/history")
        assert response.status_code == 200
        history = response.json()["history"]

        # Should have 5 records (creation + 4 transitions)
        assert len(history) == 5

        # Verify state progression
        states = [record["new_state"] for record in history]
        assert states == [
            OrderStatus.PENDING_PAYMENT,
            OrderStatus.PAID,
            OrderStatus.PROCESSING_IN_WAREHOUSE,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
        ]

    def test_order_cancellation(self, client, sample_order_data):
        """Test cancelling an order at different stages."""
        # Create order
        response = client.post("/api/v1/orders", json=sample_order_data)
        order_id = response.json()["id"]

        # Cancel while PENDING_PAYMENT
        response = client.patch(
            f"/api/v1/orders/{order_id}/state",
            json={
                "new_state": OrderStatus.CANCELLED,
                "actor": sample_order_data["customer_id"],
                "notes": "Customer requested cancellation",
            }
        )
        assert response.status_code == 200
        assert response.json()["status"] == OrderStatus.CANCELLED

        # Verify cannot transition from CANCELLED
        response = client.patch(
            f"/api/v1/orders/{order_id}/state",
            json={
                "new_state": OrderStatus.PAID,
                "actor": "SYSTEM",
            }
        )
        assert response.status_code == 400
