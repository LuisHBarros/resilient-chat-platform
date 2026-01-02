"""Factory for creating LLM provider instances based on configuration."""
from typing import Optional
from app.domain.ports.llm_port import LLMPort
from app.infrastructure.llm.openai_provider import OpenAIProvider
from app.infrastructure.llm.bedrock_provider import BedrockProvider
from app.infrastructure.llm.mock_provider import MockProvider
from app.infrastructure.config.settings import settings


def create_llm_provider(
    provider: Optional[str] = None,
    **kwargs
) -> LLMPort:
    """
    Factory function to create an LLM provider instance based on configuration.
    
    This factory follows the Dependency Inversion Principle by returning
    a domain port (LLMPort) rather than a concrete implementation.
    
    Args:
        provider: The LLM provider to use. Options: 'openai', 'bedrock', 'mock'.
                  If not provided, uses settings.llm_provider.
        **kwargs: Additional arguments passed to the provider constructor.
                  Common kwargs:
                  - api_key: For OpenAIProvider
                  - model: For OpenAIProvider
                  - model_id: For BedrockProvider
                  - region: For BedrockProvider
        
    Returns:
        An instance implementing LLMPort.
        
    Raises:
        ValueError: If provider is invalid or required configuration is missing.
    """
    # Use settings provider if not specified
    if provider is None:
        provider = settings.llm_provider.lower()
    else:
        provider = provider.lower()
    
    if provider == "openai":
        return OpenAIProvider(
            api_key=kwargs.get("api_key") or settings.openai_api_key,
            model=kwargs.get("model") or settings.openai_model,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 500)
        )
    elif provider == "bedrock":
        return BedrockProvider(
            model_id=kwargs.get("model_id") or settings.bedrock_model_id,
            region=kwargs.get("region") or settings.aws_region,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 500)
        )
    elif provider == "mock":
        return MockProvider()
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. "
            "Supported providers: 'openai', 'bedrock', 'mock'"
        )

