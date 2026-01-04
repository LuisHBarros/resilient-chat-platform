import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from jose import jwt
from app.api.routes import chat_router
from app.api.routes import chat_stream_routes
from app.api.routes import health_routes
from app.infrastructure.config.settings import settings


# Test JWT secret key (different from production)
TEST_JWT_SECRET = "test-secret-key-for-jwt-signing-do-not-use-in-production"
TEST_JWT_ALGORITHM = "HS256"


def create_test_jwt_token(user_id: str = "test-user-123", expires_in_seconds: int = 3600) -> str:
    """
    Create a test JWT token for testing purposes.
    
    This generates a JWT token signed with a test secret key that can be used
    in integration tests. The token is valid for the specified duration.
    
    Args:
        user_id: User ID to include in the token's 'sub' claim.
        expires_in_seconds: Token expiration time in seconds (default: 1 hour).
        
    Returns:
        A JWT token string.
    """
    now = datetime.utcnow()
    payload = {
        "sub": user_id,  # Subject (user ID)
        "iss": "http://test-keycloak:8080/realms/test",  # Issuer
        "aud": "chat-api",  # Audience
        "iat": int(now.timestamp()),  # Issued at
        "exp": int((now + timedelta(seconds=expires_in_seconds)).timestamp()),  # Expiration
        "typ": "Bearer",
        "azp": "chat-api",
        "realm_access": {
            "roles": ["user"]
        }
    }
    
    token = jwt.encode(payload, TEST_JWT_SECRET, algorithm=TEST_JWT_ALGORITHM)
    return token


@pytest.fixture
def test_token():
    """Fixture that provides a valid test JWT token."""
    return create_test_jwt_token()


@pytest.fixture
def test_token_with_user_id():
    """Fixture that provides a function to create tokens with custom user_id."""
    def _create_token(user_id: str = "test-user-123"):
        return create_test_jwt_token(user_id=user_id)
    return _create_token


@pytest.fixture
def mock_jwt_validator(monkeypatch):
    """
    Mock JWT validator that accepts test tokens.
    
    This fixture overrides the JWT validator to accept tokens signed with
    the test secret key, allowing integration tests to work without a real
    Keycloak instance.
    """
    from app.infrastructure.auth.jwt_validator import JWTValidator, JWTValidationError
    
    class TestJWTValidator(JWTValidator):
        """Test JWT validator that accepts test tokens."""
        
        def validate_token(self, token: str):
            """Validate test JWT token."""
            try:
                # Decode token with test secret
                payload = jwt.decode(
                    token,
                    TEST_JWT_SECRET,
                    algorithms=[TEST_JWT_ALGORITHM],
                    audience="chat-api",
                    issuer="http://test-keycloak:8080/realms/test"
                )
                return payload
            except jwt.JWTError as e:
                raise JWTValidationError(f"Token validation failed: {e}")
        
        def get_user_id(self, token: str) -> str:
            """Extract user ID from test token."""
            payload = self.validate_token(token)
            user_id = payload.get("sub")
            if not user_id:
                raise JWTValidationError("Token missing 'sub' claim (user ID)")
            return user_id
    
    # Override the get_jwt_validator function
    def get_test_validator():
        return TestJWTValidator()
    
    # Monkey patch the validator
    monkeypatch.setattr(
        "app.infrastructure.auth.jwt_validator.get_jwt_validator",
        get_test_validator
    )
    
    # Also patch in dependencies module
    monkeypatch.setattr(
        "app.api.dependencies.get_jwt_validator",
        get_test_validator
    )


@pytest.fixture
def app(mock_jwt_validator):
    """
    Create a FastAPI app instance for testing.
    
    This fixture includes all routers and sets up the mock JWT validator.
    """
    test_app = FastAPI(title="AI Platform Test")
    test_app.include_router(chat_router, prefix=settings.api_prefix)
    test_app.include_router(chat_stream_routes.router, prefix=settings.api_prefix)
    test_app.include_router(health_routes.router)
    return test_app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def authenticated_client(client, test_token):
    """
    Create a test client with authentication headers pre-configured.
    
    This fixture provides a client that automatically includes the
    Authorization header with a valid test token.
    """
    client.headers.update({
        "Authorization": f"Bearer {test_token}"
    })
    return client

