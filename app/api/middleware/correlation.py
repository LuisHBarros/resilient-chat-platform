"""Correlation ID middleware for request tracing."""
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation ID to requests.
    
    This middleware:
    1. Extracts correlation ID from X-Correlation-ID header (if present)
    2. Generates a new correlation ID if not present
    3. Adds correlation ID to request state for use in handlers
    4. Adds correlation ID to response headers
    """
    
    def __init__(self, app: ASGIApp):
        """
        Initialize correlation ID middleware.
        
        Args:
            app: The ASGI application.
        """
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and add correlation ID.
        
        Args:
            request: The incoming request.
            call_next: The next middleware/handler.
            
        Returns:
            The response with correlation ID header.
        """
        # Get correlation ID from header or generate new one
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Add to request state for use in handlers
        request.state.correlation_id = correlation_id
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response

