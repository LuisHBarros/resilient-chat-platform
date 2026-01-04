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
    
    # Keycloak Configuration
    keycloak_url: Optional[str] = None
    
    # OpenTelemetry Configuration
    otel_exporter_otlp_endpoint: Optional[str] = None
    
    # API Configuration
    api_prefix: str = "/api/v1"


# Global settings instance
settings = Settings()

