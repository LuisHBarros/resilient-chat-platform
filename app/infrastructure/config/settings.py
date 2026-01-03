"""Application settings and configuration."""
from typing import Optional, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "AI Platform"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # LLM Configuration
    llm_provider: str = "mock"
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    # LLM Fallback Configuration
    llm_fallback_enabled: bool = True
    llm_fallback_chain: Optional[List[str]] = None  # Auto-configured if None
    llm_streaming_timeout: float = 30.0  # seconds
    
    # Database Configuration
    database_url: Optional[str] = None
    
    # API Configuration
    api_prefix: str = "/api/v1"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

