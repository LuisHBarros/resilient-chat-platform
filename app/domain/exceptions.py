"""Domain exceptions.

Domain exceptions represent business rule violations and domain-level errors.
They are the base for all other exceptions in the system.
"""


class DomainException(Exception):
    """
    Base exception for domain layer.
    
    All domain exceptions should inherit from this class.
    Domain exceptions represent violations of business rules or invariants.
    """
    pass


class InvalidMessageError(DomainException):
    """Raised when a message violates domain rules (e.g., empty content)."""
    pass


class LLMError(DomainException):
    """
    Raised when LLM operation fails.
    
    Note: This is a domain exception because it represents a business-level
    failure. Infrastructure implementations should wrap their errors in this.
    """
    pass


class RepositoryError(DomainException):
    """
    Raised when repository operation fails.
    
    Note: This is a domain exception because it represents a business-level
    failure. Infrastructure implementations should wrap their errors in this.
    """
    pass

