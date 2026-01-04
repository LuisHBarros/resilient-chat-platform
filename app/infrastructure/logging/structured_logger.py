"""Structured logger implementation using Python's logging module."""
import logging
import json
import os
import logging.handlers
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
from app.domain.ports.logger_port import LoggerPort
from app.infrastructure.config.settings import settings


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields from record
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class StructuredLogger(LoggerPort):
    """
    Structured logger implementation.
    
    This logger outputs JSON-formatted logs with structured data,
    making it easy to parse and analyze logs in production.
    
    Supports:
    - Console output (default)
    - Rotating file handler (if LOG_FILE_PATH is set)
    - CloudWatch (if AWS_REGION is set and boto3 is available)
    """
    
    _initialized = False
    _file_handler = None
    _cloudwatch_handler = None
    
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
        
        # Setup handlers only once
        if not StructuredLogger._initialized:
            self._setup_handlers()
            StructuredLogger._initialized = True
    
    def _setup_handlers(self):
        """Setup logging handlers (file, CloudWatch, console)."""
        formatter = JSONFormatter()
        
        # Console handler (always enabled)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (if LOG_FILE_PATH is set)
        log_file_path = getattr(settings, "log_file_path", None)
        if log_file_path:
            try:
                log_path = Path(log_file_path)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Rotating file handler (10MB per file, keep 5 backups)
                file_handler = logging.handlers.RotatingFileHandler(
                    log_file_path,
                    maxBytes=10 * 1024 * 1024,  # 10MB
                    backupCount=5
                )
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
                StructuredLogger._file_handler = file_handler
            except Exception as e:
                # Log to console if file handler setup fails
                self.logger.warning(f"Failed to setup file handler: {e}")
        
        # CloudWatch handler (if AWS_REGION env var is set)
        aws_region = getattr(settings, "aws_region", None) or os.getenv("AWS_REGION")
        if aws_region:
            try:
                # Try to import and setup CloudWatch handler
                from watchtower import CloudWatchLogHandler
                
                cloudwatch_handler = CloudWatchLogHandler(
                    log_group_name=getattr(settings, "cloudwatch_log_group", "ai-chat-platform"),
                    stream_name=getattr(settings, "cloudwatch_log_stream", "app"),
                    use_queues=False
                )
                cloudwatch_handler.setFormatter(formatter)
                self.logger.addHandler(cloudwatch_handler)
                StructuredLogger._cloudwatch_handler = cloudwatch_handler
            except ImportError:
                # watchtower not installed, skip CloudWatch
                pass
            except Exception as e:
                # Log to console if CloudWatch setup fails
                self.logger.warning(f"Failed to setup CloudWatch handler: {e}")
    
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

