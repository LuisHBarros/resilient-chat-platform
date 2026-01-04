"""Main application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.infrastructure.config.settings import settings
from app.infrastructure.config.validation import validate_configuration
from app.api.routes import chat_router, auth_router
from app.api.routes import chat_stream_routes
from app.api.routes import health_routes
from app.api.routes import conversation_routes
from app.api.middleware.correlation import CorrelationIDMiddleware
from app.infrastructure.exceptions import ConfigurationError
from app.infrastructure.cache.redis_client import close_cache_client
import logging

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

# Prometheus imports
from prometheus_fastapi_instrumentator import Instrumentator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def setup_opentelemetry(app_instance: FastAPI):
    """
    Configure OpenTelemetry for distributed tracing.
    
    This sets up:
    - Tracer provider with resource information
    - OTLP exporter to send traces to Jaeger
    - Automatic instrumentation for FastAPI, HTTPX, and SQLAlchemy
    
    Args:
        app_instance: FastAPI application instance to instrument.
    """
    if not settings.otel_traces_enabled:
        logger.info("OpenTelemetry tracing is disabled")
        return
    
    if not settings.otel_exporter_otlp_endpoint:
        logger.warning("OpenTelemetry OTLP endpoint not configured, tracing disabled")
        return
    
    try:
        # Create resource with service information
        resource = Resource.create({
            "service.name": settings.otel_service_name,
            "service.version": settings.otel_service_version,
        })
        
        # Set up tracer provider
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)
        
        # Configure OTLP exporter (sends to Jaeger via OTLP)
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.otel_exporter_otlp_endpoint,
            insecure=True,  # Set to False in production with TLS
        )
        
        # Add span processor
        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)
        
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app_instance)
        
        # Instrument HTTPX (for external HTTP calls)
        HTTPXClientInstrumentor().instrument()
        
        # Instrument SQLAlchemy (for database queries)
        if settings.database_url:
            SQLAlchemyInstrumentor().instrument()
        
        logger.info(
            f"OpenTelemetry configured: service={settings.otel_service_name}, "
            f"endpoint={settings.otel_exporter_otlp_endpoint}"
        )
        
    except Exception as e:
        logger.error(f"Failed to configure OpenTelemetry: {e}", exc_info=True)


def setup_prometheus(app_instance: FastAPI):
    """
    Configure Prometheus metrics collection.
    
    This automatically instruments FastAPI to expose metrics at /metrics endpoint.
    Metrics include:
    - HTTP request duration
    - HTTP request count
    - HTTP request size
    - HTTP response size
    
    Args:
        app_instance: FastAPI application instance to instrument.
    """
    try:
        instrumentator = Instrumentator(
            should_group_status_codes=False,
            should_ignore_untemplated=True,
            should_instrument_requests_inprogress=True,
            excluded_handlers=["/metrics", "/health", "/health/ready"],
            inprogress_name="http_requests_inprogress",
            inprogress_labels=True,
        )
        
        instrumentator.instrument(app_instance).expose(app_instance)
        
        logger.info("Prometheus metrics configured at /metrics endpoint")
        
    except Exception as e:
        logger.error(f"Failed to configure Prometheus: {e}", exc_info=True)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# Setup observability BEFORE adding routes
setup_opentelemetry(app)
setup_prometheus(app)

# Validate configuration on startup
@app.on_event("startup")
async def startup_event():
    """Validate configuration on application startup."""
    try:
        validate_configuration()
        logger.info("Configuration validated successfully")
    except ConfigurationError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise  # Fail fast if configuration is invalid


# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on application shutdown."""
    try:
        await close_cache_client()
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.warning(f"Error during shutdown: {e}")

# Add CORS middleware (must be before other middlewares)
# Security: Use specific methods and headers instead of wildcards
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",  # Added for frontend
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",  # Added for frontend
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],  # Only allow necessary HTTP methods
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Correlation-ID",
        "Accept",
    ],  # Only allow necessary headers
    expose_headers=["X-Correlation-ID"],  # Only expose necessary headers
)

# Add middleware for correlation ID tracking
app.add_middleware(CorrelationIDMiddleware)

# Include routers
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(chat_router, prefix=settings.api_prefix)
app.include_router(chat_stream_routes.router, prefix=settings.api_prefix)
app.include_router(conversation_routes.router, prefix=settings.api_prefix)
app.include_router(health_routes.router)

# Root health check is now handled by health_routes
