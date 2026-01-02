"""Logger port for structured logging.

This port allows the domain and application layers to log without
depending on specific logging implementations (e.g., Python logging, structlog, etc.).
"""
from typing import Protocol, Optional, Any, Dict


class LoggerPort(Protocol):
    """
    Protocol defining the interface for logging implementations.
    
    This port follows the Hexagonal Architecture pattern, allowing the domain
    and application layers to log without depending on infrastructure implementations.
    """
    
    def info(self, message: str, **kwargs: Any) -> None:
        """
        Log an info message.
        
        Args:
            message: The log message.
            **kwargs: Additional structured data to include in the log.
        """
        ...
    
    def error(self, message: str, **kwargs: Any) -> None:
        """
        Log an error message.
        
        Args:
            message: The log message.
            **kwargs: Additional structured data to include in the log.
        """
        ...
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """
        Log a warning message.
        
        Args:
            message: The log message.
            **kwargs: Additional structured data to include in the log.
        """
        ...
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """
        Log a debug message.
        
        Args:
            message: The log message.
            **kwargs: Additional structured data to include in the log.
        """
        ...
    
    def with_context(self, **context: Any) -> "LoggerPort":
        """
        Create a new logger instance with additional context.
        
        This is useful for adding correlation IDs, user IDs, etc.
        
        Args:
            **context: Context data to include in all subsequent logs.
            
        Returns:
            A new logger instance with the context bound.
        """
        ...

