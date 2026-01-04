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
    
    # Database Configuration
    database_url: Optional[str] = None
    
    # Redis Configuration
    redis_url: Optional[str] = None
    
    # Rate Limiting Configuration
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60  # Default: 60 requests per minute per user
    rate_limit_window_seconds: int = 60  # Time window in seconds
    
    # Keycloak Configuration
    keycloak_url: Optional[str] = None
    keycloak_realm: str = "master"  # Default realm, should be configured per environment
    keycloak_client_id: str = "chat-api"  # Client ID registered in Keycloak
    
    # OpenTelemetry Configuration
    otel_exporter_otlp_endpoint: Optional[str] = None
    otel_service_name: str = "chat-api"  # Service name for tracing
    otel_service_version: str = "1.0.0"  # Service version for tracing
    otel_traces_enabled: bool = True  # Enable/disable tracing
    
    # API Configuration
    api_prefix: str = "/api/v1"


# Global settings instance
settings = Settings()

