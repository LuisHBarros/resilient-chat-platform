"""JWT token validation service for Magic Link Auth Service.

This module handles JWT token validation using a symmetric secret key (HS256).
It validates tokens issued by our magic link authentication microservice.
"""
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from jose.constants import ALGORITHMS
from app.infrastructure.config.settings import settings
from app.infrastructure.exceptions import InfrastructureException
import logging

logger = logging.getLogger(__name__)


class JWTValidationError(InfrastructureException):
    """Raised when JWT validation fails."""
    pass


class JWTValidator:
    """
    Validates JWT tokens issued by the Magic Link Auth Service.
    
    This class:
    - Validates JWT token signatures using a shared secret (HS256)
    - Verifies token claims (expiration, email, etc.)
    - Extracts user identity from the token
    
    Note: This uses symmetric key encryption (HS256) since both the auth service
    and backend share the same secret. For production with multiple services,
    consider using asymmetric keys (RS256) or an API validation endpoint.
    """
    
    def __init__(self):
        """Initialize the JWT validator."""
        pass
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate a JWT token and return its claims.
        
        This method:
        1. Verifies the token signature using the shared JWT secret
        2. Validates standard claims (exp, iat)
        3. Returns the decoded token payload
        
        Args:
            token: The JWT token string (without "Bearer " prefix).
            
        Returns:
            Dictionary containing the token claims (payload).
            
        Raises:
            JWTValidationError: If token validation fails for any reason.
        """
        if not token:
            raise JWTValidationError("Token is required")
        
        if not settings.jwt_secret:
            raise JWTValidationError("JWT secret is not configured. Set JWT_SECRET environment variable.")
        
        try:
            # Decode and verify token using shared secret (HS256)
            # Options:
            # - verify_signature: Verify HMAC signature
            # - verify_exp: Check expiration
            # - verify_iat: Verify issued at time
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[ALGORITHMS.HS256],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                }
            )
            
            logger.debug(
                "Token validated successfully",
                extra={
                    "email": payload.get("email"),
                    "iat": payload.get("iat"),
                }
            )
            
            return payload
            
        except JWTError as e:
            logger.warning(f"JWT validation failed: {e}")
            raise JWTValidationError(f"Token validation failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during token validation: {e}")
            raise JWTValidationError(f"Token validation error: {e}")
    
    def get_user_id(self, token: str) -> str:
        """
        Extract user ID (email) from a validated token.
        
        The magic link auth service uses email as the user identifier.
        
        Args:
            token: The JWT token string.
            
        Returns:
            The user's email address from the token.
            
        Raises:
            JWTValidationError: If token is invalid or missing email claim.
        """
        payload = self.validate_token(token)
        email = payload.get("email")
        
        if not email:
            raise JWTValidationError("Token missing 'email' claim")
        
        return email


# Global validator instance (singleton)
_validator: Optional[JWTValidator] = None


def get_jwt_validator() -> JWTValidator:
    """
    Get the global JWT validator instance.
    
    Returns:
        The global JWTValidator instance.
    """
    global _validator
    if _validator is None:
        _validator = JWTValidator()
    return _validator

