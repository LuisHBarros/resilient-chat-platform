"""Application layer exceptions."""
from app.domain.exceptions import DomainException


class ApplicationException(DomainException):
    """Base exception for application layer."""
    pass


class UseCaseError(ApplicationException):
    """Raised when a use case operation fails."""
    pass


class ValidationError(ApplicationException):
    """Raised when input validation fails in application layer."""
    pass

