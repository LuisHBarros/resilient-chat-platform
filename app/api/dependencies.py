"""API dependencies for dependency injection.

This module provides FastAPI dependency functions that use the composition root
(bootstrap.py) to resolve dependencies. This ensures all dependency resolution
happens through the composition root.
"""
from fastapi import Request, Depends
from app.bootstrap import get_container
from app.application.use_cases.process_message import ProcessMessageUseCase
from app.application.use_cases.stream_message import StreamMessageUseCase


def get_process_message_use_case(request: Request) -> ProcessMessageUseCase:
    """
    Get ProcessMessageUseCase instance with dependencies injected.
    
    This function uses the composition root to resolve all dependencies,
    ensuring proper dependency inversion and centralized composition.
    
    Args:
        request: FastAPI request for correlation ID extraction.
        
    Returns:
        ProcessMessageUseCase instance with dependencies injected.
    """
    container = get_container()
    return container.get_process_message_use_case(request)


def get_stream_message_use_case(request: Request) -> StreamMessageUseCase:
    """
    Get StreamMessageUseCase instance with dependencies injected.
    
    This function uses the composition root to resolve all dependencies
    for streaming use case.
    
    Args:
        request: FastAPI request for correlation ID extraction.
        
    Returns:
        StreamMessageUseCase instance with dependencies injected.
    """
    container = get_container()
    return container.get_stream_message_use_case(request)

