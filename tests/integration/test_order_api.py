"""
Order API integration tests.
"""
import pytest
from app.services.state_machine import OrderStatus


class TestOrderAPI:
    """Test order API endpoints."""

    def test_create_order(self, client, sample_order_data):
        """Test creating a new order."""
        response = client.post("/api/v1/orders", json=sample_order_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["customer_id"] == sample_order_data["customer_id"]
        assert data["status"] == OrderStatus.PENDING_PAYMENT
        assert "id" in data
        assert len(data["line_items"]) == 1

    def test_get_order(self, client, sample_order_data):
        """Test retrieving an order."""
        # Create order first
        create_response = client.post("/api/v1/orders", json=sample_order_data)
        order_id = create_response.json()["id"]
        
        # Get order
        response = client.get(f"/api/v1/orders/{order_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == order_id
        assert data["customer_id"] == sample_order_data["customer_id"]

    def test_get_nonexistent_order(self, client):
        """Test retrieving a nonexistent order."""
        response = client.get("/api/v1/orders/99999")
        assert response.status_code == 404

    def test_list_orders(self, client, sample_order_data):
        """Test listing orders."""
        # Create a few orders
        client.post("/api/v1/orders", json=sample_order_data)
        client.post("/api/v1/orders", json=sample_order_data)
        
        # List orders
        response = client.get("/api/v1/orders")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "page_info" in data
        assert len(data["items"]) >= 2

    def test_transition_order_state(self, client, sample_order_data):
        """Test transitioning order state."""
        # Create order
        create_response = client.post("/api/v1/orders", json=sample_order_data)
        order_id = create_response.json()["id"]
        
        # Transition to PAID
        transition_data = {
            "new_state": OrderStatus.PAID,
            "actor": "CUST123",
            "notes": "Payment received",
        }
        response = client.patch(f"/api/v1/orders/{order_id}/state", json=transition_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == OrderStatus.PAID

    def test_invalid_state_transition(self, client, sample_order_data):
        """Test invalid state transition."""
        # Create order
        create_response = client.post("/api/v1/orders", json=sample_order_data)
        order_id = create_response.json()["id"]
        
        # Try invalid transition PENDING_PAYMENT → SHIPPED
        transition_data = {
            "new_state": OrderStatus.SHIPPED,
            "actor": "SYSTEM",
        }
        response = client.patch(f"/api/v1/orders/{order_id}/state", json=transition_data)
        
        assert response.status_code == 400
        error = response.json()
        assert "error" in error
        assert error["error"]["code"] == "INVALID_STATE_TRANSITION"

    def test_get_order_history(self, client, sample_order_data):
        """Test retrieving order state history."""
        # Create order
        create_response = client.post("/api/v1/orders", json=sample_order_data)
        order_id = create_response.json()["id"]
        
        # Get history
        response = client.get(f"/api/v1/orders/{order_id}/history")
        
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert len(data["history"]) >= 1  # At least creation record
        assert data["history"][0]["new_state"] == OrderStatus.PENDING_PAYMENT
