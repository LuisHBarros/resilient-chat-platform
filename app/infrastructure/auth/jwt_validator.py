"""JWT token validation service for Keycloak.

This module handles JWT token validation using Keycloak's public keys.
It encapsulates all Keycloak-specific JWT validation logic and keeps
infrastructure concerns out of the API layer.
"""
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from jose.constants import ALGORITHMS
import httpx
from app.infrastructure.config.settings import settings
from app.infrastructure.exceptions import InfrastructureException
import logging

logger = logging.getLogger(__name__)


class JWTValidationError(InfrastructureException):
    """Raised when JWT validation fails."""
    pass


class JWTValidator:
    """
    Validates JWT tokens issued by Keycloak.
    
    This class:
    - Fetches public keys from Keycloak's JWKS endpoint
    - Validates JWT token signatures
    - Verifies token claims (expiration, audience, issuer, etc.)
    - Extracts user identity from the token
    
    The public keys are fetched on-demand and can be cached for performance.
    """
    
    def __init__(self):
        """Initialize the JWT validator."""
        self._jwks_cache: Optional[Dict[str, Any]] = None
        self._public_keys_cache: Optional[Dict[str, Any]] = None
    
    def _get_jwks_url(self) -> str:
        """
        Get the JWKS (JSON Web Key Set) URL from Keycloak.
        
        Returns:
            The JWKS endpoint URL.
            
        Raises:
            JWTValidationError: If Keycloak URL is not configured.
        """
        if not settings.keycloak_url:
            raise JWTValidationError(
                "Keycloak URL is not configured. Set KEYCLOAK_URL environment variable."
            )
        
        # Keycloak JWKS endpoint format:
        # {keycloak_url}/realms/{realm}/protocol/openid-connect/certs
        realm = settings.keycloak_realm
        base_url = settings.keycloak_url.rstrip('/')
        return f"{base_url}/realms/{realm}/protocol/openid-connect/certs"
    
    def _fetch_jwks(self) -> Dict[str, Any]:
        """
        Fetch the JWKS (JSON Web Key Set) from Keycloak.
        
        Returns:
            The JWKS containing public keys.
            
        Raises:
            JWTValidationError: If fetching JWKS fails.
        """
        jwks_url = self._get_jwks_url()
        
        try:
            logger.debug(f"Fetching JWKS from {jwks_url}")
            response = httpx.get(jwks_url, timeout=5.0)
            response.raise_for_status()
            jwks = response.json()
            
            # Cache the JWKS
            self._jwks_cache = jwks
            return jwks
        except httpx.RequestError as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            raise JWTValidationError(f"Failed to fetch JWKS from Keycloak: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Keycloak returned error status {e.response.status_code}")
            raise JWTValidationError(
                f"Keycloak JWKS endpoint returned error: {e.response.status_code}"
            )
        except Exception as e:
            logger.error(f"Unexpected error fetching JWKS: {e}")
            raise JWTValidationError(f"Unexpected error fetching JWKS: {e}")
    
    def _get_public_key(self, token: str) -> str:
        """
        Get the public key for verifying the JWT token.
        
        Args:
            token: The JWT token (header is used to find the key).
            
        Returns:
            The public key in PEM format.
            
        Raises:
            JWTValidationError: If the key cannot be found or extracted.
        """
        # Decode token header (without verification) to get the key ID (kid)
        try:
            unverified_header = jwt.get_unverified_header(token)
        except JWTError as e:
            raise JWTValidationError(f"Invalid token header: {e}")
        
        kid = unverified_header.get("kid")
        if not kid:
            raise JWTValidationError("Token header missing 'kid' (key ID)")
        
        # Fetch JWKS if not cached
        if self._jwks_cache is None:
            self._fetch_jwks()
        
        # Find the key with matching kid
        jwks = self._jwks_cache
        key = None
        for jwk in jwks.get("keys", []):
            if jwk.get("kid") == kid:
                key = jwk
                break
        
        if not key:
            # Try refreshing JWKS in case keys rotated
            logger.warning(f"Key with kid={kid} not found in cache, refreshing JWKS")
            self._jwks_cache = None
            jwks = self._fetch_jwks()
            for jwk in jwks.get("keys", []):
                if jwk.get("kid") == kid:
                    key = jwk
                    break
        
        if not key:
            raise JWTValidationError(f"Public key with kid={kid} not found in JWKS")
        
        # Convert JWK to PEM format
        try:
            from jose.utils import base64url_decode
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import serialization
            
            # Extract RSA components from JWK (base64url encoded)
            n_bytes = base64url_decode(key["n"])
            e_bytes = base64url_decode(key["e"])
            
            # Convert bytes to integers (big-endian)
            n_int = int.from_bytes(n_bytes, 'big')
            e_int = int.from_bytes(e_bytes, 'big')
            
            # Reconstruct RSA public key
            public_numbers = rsa.RSAPublicNumbers(e_int, n_int)
            public_key = public_numbers.public_key(default_backend())
            
            # Serialize to PEM format
            pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            return pem.decode('utf-8')
        except KeyError as e:
            logger.error(f"JWK missing required field: {e}")
            raise JWTValidationError(f"JWK missing required field: {e}")
        except Exception as e:
            logger.error(f"Failed to convert JWK to PEM: {e}")
            raise JWTValidationError(f"Failed to extract public key: {e}")
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate a JWT token and return its claims.
        
        This method:
        1. Fetches the public key from Keycloak's JWKS endpoint
        2. Verifies the token signature
        3. Validates standard claims (exp, iat, aud, iss)
        4. Returns the decoded token payload
        
        Args:
            token: The JWT token string (without "Bearer " prefix).
            
        Returns:
            Dictionary containing the token claims (payload).
            
        Raises:
            JWTValidationError: If token validation fails for any reason.
        """
        if not token:
            raise JWTValidationError("Token is required")
        
        try:
            # Get public key for verification
            public_key = self._get_public_key(token)
            
            # Build expected issuer URL
            if not settings.keycloak_url:
                raise JWTValidationError("Keycloak URL not configured")
            
            realm = settings.keycloak_realm
            base_url = settings.keycloak_url.rstrip('/')
            expected_issuer = f"{base_url}/realms/{realm}"
            
            # Expected audience (client ID)
            expected_audience = settings.keycloak_client_id
            
            # Decode and verify token
            # Options:
            # - verify_signature: Verify RSA signature
            # - verify_exp: Check expiration
            # - verify_aud: Check audience matches client_id
            # - verify_iss: Check issuer matches Keycloak realm
            payload = jwt.decode(
                token,
                public_key,
                algorithms=[ALGORITHMS.RS256],
                audience=expected_audience,
                issuer=expected_issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True,
                }
            )
            
            logger.debug(
                "Token validated successfully",
                extra={
                    "sub": payload.get("sub"),
                    "iss": payload.get("iss"),
                    "aud": payload.get("aud"),
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
        Extract user ID (sub claim) from a validated token.
        
        Args:
            token: The JWT token string.
            
        Returns:
            The user ID (sub claim) from the token.
            
        Raises:
            JWTValidationError: If token is invalid or missing sub claim.
        """
        payload = self.validate_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise JWTValidationError("Token missing 'sub' claim (user ID)")
        
        return user_id
    
    def clear_cache(self):
        """Clear the JWKS cache (useful for testing or key rotation)."""
        self._jwks_cache = None
        self._public_keys_cache = None


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

