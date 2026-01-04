"""API dependencies for dependency injection.

This module provides FastAPI dependency functions that use the composition root
(bootstrap.py) to resolve dependencies. This ensures all dependency resolution
happens through the composition root.
"""
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.bootstrap import get_container
from app.application.use_cases.process_message import ProcessMessageUseCase
from app.application.use_cases.stream_message import StreamMessageUseCase
from app.infrastructure.auth.jwt_validator import get_jwt_validator, JWTValidationError
from app.infrastructure.cache.redis_client import get_cache_client
from app.infrastructure.config.settings import settings
from app.domain.ports.cache_port import CachePort
import logging

logger = logging.getLogger(__name__)

# HTTPBearer security scheme for extracting Bearer tokens
security = HTTPBearer()


def get_authenticated_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    FastAPI dependency that validates JWT token and returns authenticated user ID.
    
    This guard:
    1. Extracts the JWT from the Authorization: Bearer <token> header
    2. Validates the token using Keycloak's public key
    3. Extracts the user ID (sub claim) from the token
    4. Returns the user ID to be used in route handlers
    
    Args:
        credentials: HTTPAuthorizationCredentials containing the Bearer token.
        
    Returns:
        The authenticated user ID (sub claim from JWT).
        
    Raises:
        HTTPException: If token is missing, invalid, or expired.
    """
    try:
        # Extract token from Bearer credentials
        token = credentials.credentials
        
        # Validate token and get user ID
        validator = get_jwt_validator()
        user_id = validator.get_user_id(token)
        
        return user_id
        
    except JWTValidationError as e:
        # Token validation failed
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        # Unexpected error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}",
        )


def get_process_message_use_case(request: Request) -> ProcessMessageUseCase:
    """
    Get ProcessMessageUseCase instance with dependencies injected.
    
    This function uses the composition root to resolve all dependencies,
    ensuring proper dependency inversion and centralized composition.
    
    Args:
        request: FastAPI request for correlation ID extraction.
        
    Returns:
        ProcessMessageUseCase instance with dependencies injected.
    """
    container = get_container()
    return container.get_process_message_use_case(request)


def get_stream_message_use_case(request: Request) -> StreamMessageUseCase:
    """
    Get StreamMessageUseCase instance with dependencies injected.
    
    This function uses the composition root to resolve all dependencies
    for streaming use case.
    
    Args:
        request: FastAPI request for correlation ID extraction.
        
    Returns:
        StreamMessageUseCase instance with dependencies injected.
    """
    container = get_container()
    return container.get_stream_message_use_case(request)


async def check_rate_limit(user_id: str = Depends(get_authenticated_user_id)) -> None:
    """
    FastAPI dependency that enforces rate limiting per user.
    
    This rate limiter uses Redis to track request counts per user within
    a sliding time window. It implements a token bucket-like algorithm
    using Redis atomic operations.
    
    Rate limiting is applied per user (user_id) and is configurable via:
    - RATE_LIMIT_REQUESTS_PER_MINUTE: Maximum requests allowed
    - RATE_LIMIT_WINDOW_SECONDS: Time window in seconds
    
    Args:
        user_id: Authenticated user ID (from JWT token, injected via dependency).
        
    Raises:
        HTTPException: If rate limit is exceeded (429 Too Many Requests).
    """
    # Skip rate limiting if disabled
    if not settings.rate_limit_enabled:
        return
    
    # Get cache client (Redis)
    cache = get_cache_client()
    if not cache:
        # Redis not available, allow request through (fail open)
        logger.warning("Rate limiting enabled but Redis not available, allowing request")
        return
    
    # Build rate limit key: "rate_limit:{user_id}"
    rate_limit_key = f"rate_limit:{user_id}"
    
    try:
        # Get current request count
        current_count = await cache.increment(
            key=rate_limit_key,
            amount=1,
            ttl_seconds=settings.rate_limit_window_seconds
        )
        
        # Check if limit exceeded
        max_requests = settings.rate_limit_requests_per_minute
        
        if current_count > max_requests:
            # Calculate retry-after (seconds until window resets)
            # Since we use TTL, we can estimate based on window size
            retry_after = settings.rate_limit_window_seconds
            
            logger.warning(
                f"Rate limit exceeded for user {user_id}: {current_count}/{max_requests} requests"
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {max_requests} requests per {settings.rate_limit_window_seconds} seconds.",
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": str(max(0, max_requests - current_count)),
                    "X-RateLimit-Reset": str(retry_after),
                },
            )
        
        # Log rate limit status (debug level)
        logger.debug(
            f"Rate limit check passed for user {user_id}: {current_count}/{max_requests} requests"
        )
        
    except HTTPException:
        # Re-raise rate limit exceptions
        raise
    except Exception as e:
        # On error, allow request through (fail open)
        logger.error(f"Rate limit check error for user {user_id}: {e}")
        # Don't block requests if rate limiting fails

