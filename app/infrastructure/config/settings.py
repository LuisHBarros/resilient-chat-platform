"""Application settings and configuration."""
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields from .env (e.g., POSTGRES_USER used by docker-compose)
    )
    
    # Application
    app_name: str = "AI Platform"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # LLM Configuration
    llm_provider: str = "mock"
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"
    
    # LLM Fallback Configuration
    llm_fallback_enabled: bool = True
    llm_fallback_chain: Optional[List[str]] = None  # Auto-configured if None
    llm_streaming_timeout: float = 30.0  # seconds
    llm_failure_cooldown: int = 300  # seconds (5 minutes) - cooldown for failed models
    llm_circuit_breaker_enabled: bool = True  # Enable circuit breaker for LLM calls
    llm_circuit_breaker_failure_threshold: int = 5  # Failures before opening circuit
    llm_circuit_breaker_recovery_timeout: int = 60  # seconds before attempting recovery
    
    # Database Configuration
    database_url: Optional[str] = None
    db_pool_size: int = 10  # Number of connections to maintain in pool
    db_max_overflow: int = 20  # Maximum overflow connections
    db_pool_timeout: int = 30  # Seconds to wait for connection from pool
    db_pool_recycle: int = 3600  # Seconds before recycling connections
    
    # Redis Configuration
    redis_url: Optional[str] = None
    
    # Rate Limiting Configuration
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60  # Default: 60 requests per minute per user
    rate_limit_window_seconds: int = 60  # Time window in seconds
    
    # JWT Authentication Configuration (for Magic Link Auth Service)
    jwt_secret: Optional[str] = None  # Shared secret with auth-service for JWT validation
    
    # OpenTelemetry Configuration
    otel_exporter_otlp_endpoint: Optional[str] = None
    otel_service_name: str = "chat-api"  # Service name for tracing
    otel_service_version: str = "1.0.0"  # Service version for tracing
    otel_traces_enabled: bool = True  # Enable/disable tracing
    
    # API Configuration
    api_prefix: str = "/api/v1"


# Global settings instance
settings = Settings()

