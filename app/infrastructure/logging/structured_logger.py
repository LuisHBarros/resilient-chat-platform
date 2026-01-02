"""Structured logger implementation using Python's logging module."""
import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime
from app.domain.ports.logger_port import LoggerPort


class StructuredLogger(LoggerPort):
    """
    Structured logger implementation.
    
    This logger outputs JSON-formatted logs with structured data,
    making it easy to parse and analyze logs in production.
    """
    
    def __init__(
        self,
        name: str = "app",
        level: int = logging.INFO,
        correlation_id: Optional[str] = None
    ):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name.
            level: Logging level.
            correlation_id: Optional correlation ID for request tracing.
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self._context: Dict[str, Any] = {}
        
        if correlation_id:
            self._context["correlation_id"] = correlation_id
    
    def _log(self, level: int, message: str, **kwargs: Any) -> None:
        """
        Internal method to log with structured data.
        
        Args:
            level: Logging level.
            message: Log message.
            **kwargs: Additional structured data.
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": logging.getLevelName(level),
            "message": message,
            **self._context,
            **kwargs
        }
        
        # Output as JSON for structured logging
        self.logger.log(level, json.dumps(log_data))
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message."""
        self._log(logging.INFO, message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message."""
        self._log(logging.ERROR, message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message."""
        self._log(logging.WARNING, message, **kwargs)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message."""
        self._log(logging.DEBUG, message, **kwargs)
    
    def with_context(self, **context: Any) -> "StructuredLogger":
        """
        Create a new logger instance with additional context.
        
        Args:
            **context: Context data to include in all subsequent logs.
            
        Returns:
            A new logger instance with the context bound.
        """
        new_logger = StructuredLogger(
            name=self.logger.name,
            level=self.logger.level
        )
        new_logger._context = {**self._context, **context}
        return new_logger


class NullLogger(LoggerPort):
    """
    Null logger implementation that discards all logs.
    
    Useful for testing or when logging is not needed.
    """
    
    def info(self, message: str, **kwargs: Any) -> None:
        """No-op."""
        pass
    
    def error(self, message: str, **kwargs: Any) -> None:
        """No-op."""
        pass
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """No-op."""
        pass
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """No-op."""
        pass
    
    def with_context(self, **context: Any) -> "LoggerPort":
        """Return self (no context to add)."""
        return self

