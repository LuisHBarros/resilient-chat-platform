import pytest
from fastapi import status
from fastapi.testclient import TestClient
from tests.conftest import create_test_jwt_token


class TestMessageEndpoint:
    """Integration tests for POST /chat/message endpoint."""

    def test_post_message_success(self, authenticated_client: TestClient):
        """Test successful message submission with authentication."""
        response = authenticated_client.post(
            "/api/v1/chat/message",
            json={"message": "Hello, AI!"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "response" in data
        assert isinstance(data["response"], str)
        assert "conversation_id" in data

    def test_post_message_without_auth(self, client: TestClient):
        """Test that message submission without auth token fails."""
        response = client.post(
            "/api/v1/chat/message",
            json={"message": "Hello, AI!"}
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_message_invalid_token(self, client: TestClient):
        """Test that message submission with invalid token fails."""
        response = client.post(
            "/api/v1/chat/message",
            json={"message": "Hello, AI!"},
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_post_message_empty_string(self, authenticated_client: TestClient):
        """Test message submission with empty string."""
        response = authenticated_client.post(
            "/api/v1/chat/message",
            json={"message": ""}
        )
        
        # Empty string should be rejected by validation
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST
        ]

    def test_post_message_missing_field(self, authenticated_client: TestClient):
        """Test message submission with missing message field."""
        response = authenticated_client.post(
            "/api/v1/chat/message",
            json={}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data

    def test_post_message_invalid_type(self, authenticated_client: TestClient):
        """Test message submission with invalid type."""
        response = authenticated_client.post(
            "/api/v1/chat/message",
            json={"message": 123}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_post_message_long_message(self, authenticated_client: TestClient):
        """Test message submission with long message."""
        long_message = "A" * 1000
        response = authenticated_client.post(
            "/api/v1/chat/message",
            json={"message": long_message}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "response" in data

    def test_post_message_special_characters(self, authenticated_client: TestClient):
        """Test message submission with special characters."""
        special_message = "Hello! @#$%^&*() 中文 🚀"
        response = authenticated_client.post(
            "/api/v1/chat/message",
            json={"message": special_message}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "response" in data

    def test_post_message_wrong_method(self, authenticated_client: TestClient):
        """Test that GET method is not allowed on /chat/message endpoint."""
        response = authenticated_client.get("/api/v1/chat/message")
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_post_message_different_users(self, client: TestClient, test_token_with_user_id):
        """Test that different users get different conversations."""
        # User 1
        token1 = test_token_with_user_id("user-1")
        response1 = client.post(
            "/api/v1/chat/message",
            json={"message": "Hello from user 1"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        assert response1.status_code == status.HTTP_200_OK
        conv_id_1 = response1.json()["conversation_id"]
        
        # User 2
        token2 = test_token_with_user_id("user-2")
        response2 = client.post(
            "/api/v1/chat/message",
            json={"message": "Hello from user 2"},
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert response2.status_code == status.HTTP_200_OK
        conv_id_2 = response2.json()["conversation_id"]
        
        # Conversations should be different
        assert conv_id_1 != conv_id_2


class TestHealthEndpoint:
    """Integration tests for GET /chat/health endpoint."""

    def test_get_health_success(self, client: TestClient):
        """Test successful health check."""
        response = client.get("/api/v1/chat/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == {"status": "ok"}

    def test_get_health_wrong_method(self, client: TestClient):
        """Test that POST method is not allowed on /chat/health endpoint."""
        response = client.post("/api/v1/chat/health")
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_get_health_multiple_calls(self, client: TestClient):
        """Test that health endpoint works with multiple calls."""
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == status.HTTP_200_OK
            assert response.json() == {"status": "ok"}

