"""Health check routes."""
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.bootstrap import get_container
from app.domain.ports.llm_port import LLMPort
from app.domain.ports.repository_port import RepositoryPort


router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    """
    Basic health check endpoint.
    
    Returns:
        Simple status indicating the service is running.
    """
    return {"status": "ok"}


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    
    This endpoint verifies that the service is ready to handle requests by:
    - Checking LLM provider connectivity
    - Checking repository/database connectivity
    
    Returns:
        JSONResponse with status and component checks.
    """
    container = get_container()
    checks = {
        "status": "ready",
        "checks": {}
    }
    all_healthy = True
    
    # Check LLM provider with real connectivity test
    try:
        llm = container.get_llm()
        
        # Test real connectivity by attempting to generate a minimal response
        # Use a timeout to avoid hanging
        import asyncio
        
        try:
            # For MockProvider, this will work immediately
            # For real providers, this tests actual API connectivity
            test_response = await asyncio.wait_for(
                llm.generate("test"),
                timeout=5.0  # 5 second timeout for health check
            )
            checks["checks"]["llm"] = {
                "status": "healthy",
                "response_received": bool(test_response)
            }
        except asyncio.TimeoutError:
            checks["checks"]["llm"] = {
                "status": "unhealthy",
                "error": "LLM provider timeout (no response within 5 seconds)"
            }
            all_healthy = False
        except Exception as llm_error:
            # Check if it's a configuration error (acceptable for health check)
            error_str = str(llm_error).lower()
            if "api key" in error_str or "credentials" in error_str or "configuration" in error_str:
                checks["checks"]["llm"] = {
                    "status": "unhealthy",
                    "error": "LLM provider configuration error",
                    "details": str(llm_error)
                }
            else:
                checks["checks"]["llm"] = {
                    "status": "unhealthy",
                    "error": f"LLM provider error: {str(llm_error)}"
                }
            all_healthy = False
    except Exception as e:
        checks["checks"]["llm"] = {
            "status": "unhealthy",
            "error": f"Failed to initialize LLM provider: {str(e)}"
        }
        all_healthy = False
    
    # Check repository with real connectivity test
    try:
        repository = container.get_repository()
        
        # Test real database connectivity
        # For PostgresRepository, use the connection test method
        if hasattr(repository, "_test_connection"):
            is_healthy = await repository._test_connection()
            if is_healthy:
                checks["checks"]["repository"] = {"status": "healthy"}
            else:
                checks["checks"]["repository"] = {
                    "status": "unhealthy",
                    "error": "Database connection test failed"
                }
                all_healthy = False
        else:
            # For InMemoryRepository, just verify it's initialized
            # Try a simple operation
            await repository.find_by_id("health-check-test-id")
            checks["checks"]["repository"] = {"status": "healthy"}
    except Exception as e:
        # If it's a "not found" error, that's fine - repository is working
        error_str = str(e).lower()
        if "not found" in error_str or "none" in error_str:
            checks["checks"]["repository"] = {"status": "healthy"}
        elif "connection" in error_str or "timeout" in error_str:
            checks["checks"]["repository"] = {
                "status": "unhealthy",
                "error": f"Database connectivity error: {str(e)}"
            }
            all_healthy = False
        else:
            checks["checks"]["repository"] = {
                "status": "unhealthy",
                "error": f"Repository error: {str(e)}"
            }
            all_healthy = False
    
    # Set overall status
    if not all_healthy:
        checks["status"] = "not_ready"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=checks
        )
    
    return checks

