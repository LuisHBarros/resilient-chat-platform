"""Composition root for dependency injection.

This module is responsible for composing all dependencies and creating
the application's object graph. It follows the Composition Root pattern,
ensuring that dependency resolution happens at the application's entry point.

All adapters, services, and use cases are wired together here.
"""
from typing import Optional
from fastapi import Request

from app.domain.ports.llm_port import LLMPort
from app.domain.ports.repository_port import RepositoryPort
from app.domain.ports.logger_port import LoggerPort
from app.application.use_cases.process_message import ProcessMessageUseCase
from app.application.use_cases.stream_message import StreamMessageUseCase

# Infrastructure implementations
from app.infrastructure.llm.factory import create_llm_provider
from app.infrastructure.persistence import InMemoryRepository, PostgresRepository
from app.infrastructure.logging import StructuredLogger, NullLogger
from app.infrastructure.config.settings import settings


class ApplicationContainer:
    """
    Application container that holds all dependencies.
    
    This container follows the Composition Root pattern, centralizing
    all dependency creation and wiring. This ensures:
    1. Dependencies are created in one place
    2. Easy to swap implementations
    3. Clear dependency graph
    """
    
    def __init__(self):
        """Initialize the application container."""
        self._llm: Optional[LLMPort] = None
        self._repository: Optional[RepositoryPort] = None
    
    def get_llm(self) -> LLMPort:
        """
        Get LLM provider instance (singleton).
        
        Returns:
            LLM provider implementing LLMPort.
        """
        if self._llm is None:
            self._llm = create_llm_provider()
        return self._llm
    
    def get_repository(self) -> RepositoryPort:
        """
        Get repository instance (singleton).
        
        Uses PostgresRepository if DATABASE_URL is configured,
        otherwise falls back to InMemoryRepository.
        
        Returns:
            Repository implementing RepositoryPort.
        """
        if self._repository is None:
            if settings.database_url:
                self._repository = PostgresRepository()
            else:
                self._repository = InMemoryRepository()
        return self._repository
    
    def get_logger(self, request: Optional[Request] = None) -> LoggerPort:
        """
        Get logger instance with optional correlation ID.
        
        Args:
            request: Optional FastAPI request to extract correlation ID.
            
        Returns:
            Logger implementing LoggerPort.
        """
        correlation_id = None
        if request and hasattr(request.state, "correlation_id"):
            correlation_id = request.state.correlation_id
        
        if correlation_id:
            return StructuredLogger(correlation_id=correlation_id)
        return StructuredLogger()
    
    def get_process_message_use_case(
        self,
        request: Optional[Request] = None
    ) -> ProcessMessageUseCase:
        """
        Get ProcessMessageUseCase with all dependencies injected.
        
        This is the main composition method that wires together:
        - LLM provider
        - Repository
        - Logger (with correlation ID if available)
        
        Note: Use case is created per-request to ensure logger has correct
        correlation ID. LLM and Repository are singletons for performance.
        
        Args:
            request: Optional FastAPI request for correlation ID.
            
        Returns:
            ProcessMessageUseCase instance with dependencies injected.
        """
        llm = self.get_llm()
        repository = self.get_repository()
        logger = self.get_logger(request)
        
        return ProcessMessageUseCase(
            llm=llm,
            repository=repository,
            logger=logger
        )
    
    def get_stream_message_use_case(
        self,
        request: Optional[Request] = None
    ) -> StreamMessageUseCase:
        """
        Get StreamMessageUseCase with all dependencies injected.
        
        This method wires up the streaming use case with its dependencies.
        Use case is created per-request to ensure logger has correct
        correlation ID.
        
        Args:
            request: Optional FastAPI request for correlation ID.
            
        Returns:
            StreamMessageUseCase instance with dependencies injected.
        """
        llm = self.get_llm()
        repository = self.get_repository()
        logger = self.get_logger(request)
        
        return StreamMessageUseCase(
            llm=llm,
            repository=repository,
            logger=logger
        )
    
    def reset(self):
        """
        Reset all dependencies (useful for testing).
        
        This clears all cached instances, forcing recreation on next access.
        """
        self._llm = None
        self._repository = None


# Global container instance
_container = ApplicationContainer()


def get_container() -> ApplicationContainer:
    """
    Get the global application container.
    
    Returns:
        The global ApplicationContainer instance.
    """
    return _container


def reset_container():
    """Reset the global container (useful for testing)."""
    _container.reset()

