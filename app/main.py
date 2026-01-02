"""Main application entry point."""
from fastapi import FastAPI
from app.infrastructure.config.settings import settings
from app.api.routes import chat_router
from app.api.middleware.correlation import CorrelationIDMiddleware

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# Add middleware for correlation ID tracking
app.add_middleware(CorrelationIDMiddleware)

# Include routers
app.include_router(chat_router, prefix=settings.api_prefix)

@app.get("/health")
def health():
    """Root health check endpoint."""
    return {"status": "ok", "version": settings.app_version}
