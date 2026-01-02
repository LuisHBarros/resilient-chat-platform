"""Chat API routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.api.dto.chat_dto import MessageRequestDTO, MessageResponseDTO
from app.api.dependencies import get_process_message_use_case
from app.application.use_cases.process_message import ProcessMessageUseCase
from app.domain.exceptions import LLMError, RepositoryError
from app.application.exceptions import ApplicationException
from app.infrastructure.exceptions import InfrastructureException


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=MessageResponseDTO)
async def send_message(
    payload: MessageRequestDTO,
    request: Request,
    use_case: ProcessMessageUseCase = Depends(get_process_message_use_case)
):
    """
    Send a message and get AI response.
    
    Args:
        payload: The message request DTO.
        use_case: Injected process message use case.
        
    Returns:
        MessageResponseDTO with the generated response.
        
    Raises:
        HTTPException: If processing fails.
    """
    try:
        result = await use_case.execute(
            user_id=payload.user_id or "default_user",
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

