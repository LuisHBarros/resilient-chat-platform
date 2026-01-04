"""Chat API routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.api.dto.chat_dto import MessageRequestDTO, MessageResponseDTO
from app.api.dependencies import (
    get_process_message_use_case,
    get_authenticated_user_id,
    check_rate_limit
)
from app.application.use_cases.process_message import ProcessMessageUseCase
from app.domain.exceptions import LLMError, RepositoryError
from app.application.exceptions import ApplicationException
from app.infrastructure.exceptions import InfrastructureException


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=MessageResponseDTO)
async def send_message(
    payload: MessageRequestDTO,
    request: Request,
    user_id: str = Depends(get_authenticated_user_id),
    _: None = Depends(check_rate_limit),  # Rate limiting (uses user_id from above)
    use_case: ProcessMessageUseCase = Depends(get_process_message_use_case)
):
    """
    Send a message and get AI response.
    
    This endpoint requires authentication via JWT token in the Authorization header.
    The user ID is automatically extracted from the token - it should NOT be provided
    in the request body.
    
    Args:
        payload: The message request DTO (without user_id).
        request: FastAPI request object.
        user_id: Authenticated user ID extracted from JWT token (injected via dependency).
        use_case: Injected process message use case.
        
    Returns:
        MessageResponseDTO with the generated response.
        
    Raises:
        HTTPException: If authentication fails or processing fails.
    """
    try:
        result = await use_case.execute(
            user_id=user_id,
            message_content=payload.message,
            conversation_id=payload.conversation_id
        )
        
        return MessageResponseDTO(
            conversation_id=result["conversation_id"],
            response=result["response"],
            user_message=result["user_message"],
            assistant_message=result["assistant_message"]
        )
    except LLMError as e:
        # Domain exception: LLM operation failed
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM service error: {str(e)}"
        )
    except RepositoryError as e:
        # Domain exception: Repository operation failed
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Repository error: {str(e)}"
        )
    except ApplicationException as e:
        # Application layer exception
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Application error: {str(e)}"
        )
    except InfrastructureException as e:
        # Infrastructure layer exception
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Infrastructure error: {str(e)}"
        )
    except Exception as e:
        # Unexpected error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

