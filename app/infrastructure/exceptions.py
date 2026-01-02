"""Infrastructure layer exceptions."""
from app.domain.exceptions import DomainException


class InfrastructureException(DomainException):
    """Base exception for infrastructure layer."""
    pass


class LLMProviderError(InfrastructureException):
    """Raised when LLM provider operation fails."""
    pass


class DatabaseError(InfrastructureException):
    """Raised when database operation fails."""
    pass


class ConfigurationError(InfrastructureException):
    """Raised when configuration is invalid or missing."""
    pass

