"""
Return API integration tests.
"""
import pytest
from app.services.state_machine import ReturnStatus, OrderStatus


class TestReturnAPI:
    """Test return request API endpoints."""

    @pytest.fixture
    def created_order(self, client, sample_order_data):
        """Create an order for testing returns."""
        response = client.post("/api/v1/orders", json=sample_order_data)
        assert response.status_code == 201
        order = response.json()
        
        # Transition to DELIVERED (returns only allowed on delivered orders)
        transitions = [OrderStatus.PAID, OrderStatus.PROCESSING_IN_WAREHOUSE, OrderStatus.SHIPPED, OrderStatus.DELIVERED]
        for state in transitions:
            client.patch(
                f"/api/v1/orders/{order['id']}/state",
                json={"new_state": state, "actor": "SYSTEM"}
            )
        
        return order

    def test_create_return(self, client, created_order):
        """Test creating a return request."""
        return_data = {
            "order_id": created_order["id"],
            "reason": "Product damaged",
            "requested_by": created_order["customer_id"],
            "items": [{"line_item_id": created_order["line_items"][0]["id"], "quantity": 1}],
            "refund_amount": "25.00",
        }
        
        response = client.post("/api/v1/returns", json=return_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["order_id"] == created_order["id"]
        assert data["status"] == ReturnStatus.REQUESTED
        assert data["reason"] == "Product damaged"

    def test_get_return(self, client, created_order):
        """Test retrieving a return request."""
        # Create return first
        return_data = {
            "order_id": created_order["id"],
            "reason": "Test reason",
            "requested_by": created_order["customer_id"],
            "items": [{"line_item_id": created_order["line_items"][0]["id"], "quantity": 1}],
            "refund_amount": "25.00",
        }
        create_response = client.post("/api/v1/returns", json=return_data)
        return_id = create_response.json()["id"]
        
        # Get return
        response = client.get(f"/api/v1/returns/{return_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == return_id
        assert data["order_id"] == created_order["id"]

    def test_approve_return(self, client, created_order):
        """Test approving a return request."""
        # Create return
        return_data = {
            "order_id": created_order["id"],
            "reason": "Test reason",
            "requested_by": created_order["customer_id"],
            "items": [{"line_item_id": created_order["line_items"][0]["id"], "quantity": 1}],
            "refund_amount": "25.00",
        }
        create_response = client.post("/api/v1/returns", json=return_data)
        return_id = create_response.json()["id"]
        
        # Approve return
        approval_data = {
            "approved_by": "ADMIN001",
            "notes": "Approval granted",
        }
        response = client.patch(f"/api/v1/returns/{return_id}/approve", json=approval_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == ReturnStatus.APPROVED
        assert data["approved_by"] == "ADMIN001"

    def test_reject_return(self, client, created_order):
        """Test rejecting a return request."""
        # Create return
        return_data = {
            "order_id": created_order["id"],
            "reason": "Test reason",
            "requested_by": created_order["customer_id"],
            "items": [{"line_item_id": created_order["line_items"][0]["id"], "quantity": 1}],
            "refund_amount": "25.00",
        }
        create_response = client.post("/api/v1/returns", json=return_data)
        return_id = create_response.json()["id"]
        
        # Reject return
        rejection_data = {
            "rejected_by": "ADMIN001",
            "rejection_reason": "Outside return window",
        }
        response = client.patch(f"/api/v1/returns/{return_id}/reject", json=rejection_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == ReturnStatus.REJECTED
        assert data["rejection_reason"] == "Outside return window"

    def test_list_returns(self, client, created_order):
        """Test listing returns."""
        # Create a couple of returns
        return_data = {
            "order_id": created_order["id"],
            "reason": "Test reason",
            "requested_by": created_order["customer_id"],
            "items": [{"line_item_id": created_order["line_items"][0]["id"], "quantity": 1}],
            "refund_amount": "25.00",
        }
        client.post("/api/v1/returns", json=return_data)
        client.post("/api/v1/returns", json=return_data)
        
        # List returns
        response = client.get("/api/v1/returns")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "page_info" in data
        assert len(data["items"]) >= 2

    def test_get_return_history(self, client, created_order):
        """Test retrieving return state history."""
        # Create return
        return_data = {
            "order_id": created_order["id"],
            "reason": "Test reason",
            "requested_by": created_order["customer_id"],
            "items": [{"line_item_id": created_order["line_items"][0]["id"], "quantity": 1}],
            "refund_amount": "25.00",
        }
        create_response = client.post("/api/v1/returns", json=return_data)
        return_id = create_response.json()["id"]
        
        # Get history
        response = client.get(f"/api/v1/returns/{return_id}/history")
        
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert len(data["history"]) >= 1
        assert data["history"][0]["new_state"] == ReturnStatus.REQUESTED
