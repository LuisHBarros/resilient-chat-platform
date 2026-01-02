"""Chat streaming API routes (SSE)."""
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import StreamingResponse
from app.api.dto.chat_dto import MessageRequestDTO
from app.api.dependencies import get_stream_message_use_case
from app.application.use_cases.stream_message import StreamMessageUseCase
from app.domain.exceptions import LLMError, RepositoryError
from app.application.exceptions import ApplicationException
from app.infrastructure.exceptions import InfrastructureException
import json


router = APIRouter(prefix="/chat", tags=["chat"])


async def _format_sse_stream(use_case: StreamMessageUseCase, user_id: str, message: str, conversation_id: str = None):
    """
    Stream message processing and format as SSE.
    
    This function uses the StreamMessageUseCase to:
    1. Save user message
    2. Stream LLM response chunks
    3. Save assistant message
    
    Args:
        use_case: StreamMessageUseCase instance.
        user_id: User identifier.
        message: Message content.
        conversation_id: Optional conversation ID.
        
    Yields:
        SSE-formatted chunks.
    """
    try:
        # Stream chunks from use case
        async for chunk in use_case.execute(
            user_id=user_id,
            message_content=message,
            conversation_id=conversation_id
        ):
            # Format as SSE (Server-Sent Events)
            data = json.dumps({"chunk": chunk})
            yield f"data: {data}\n\n"
        
        # Send completion event
        yield f"data: {json.dumps({'done': True})}\n\n"
    except LLMError as e:
        # Send error event
        error_data = json.dumps({"error": str(e), "type": "llm_error"})
        yield f"data: {error_data}\n\n"
    except RepositoryError as e:
        # Send error event
        error_data = json.dumps({"error": str(e), "type": "repository_error"})
        yield f"data: {error_data}\n\n"
    except Exception as e:
        # Send unexpected error event
        error_data = json.dumps({"error": str(e), "type": "unexpected_error"})
        yield f"data: {error_data}\n\n"


@router.post("/message/stream")
async def stream_message(
    payload: MessageRequestDTO,
    request: Request,
    use_case: StreamMessageUseCase = Depends(get_stream_message_use_case)
):
    """
    Stream AI response using Server-Sent Events (SSE).
    
    This endpoint:
    - Saves user message immediately
    - Streams LLM response in real-time
    - Saves assistant message when complete
    
    This ensures data persistence while providing streaming UX.
    
    Args:
        payload: The message request DTO.
        request: FastAPI request for correlation ID.
        use_case: Injected StreamMessageUseCase.
        
    Returns:
        StreamingResponse with SSE-formatted chunks.
        
    Raises:
        HTTPException: If use case setup fails (before streaming starts).
    """
    try:
        return StreamingResponse(
            _format_sse_stream(
                use_case=use_case,
                user_id=payload.user_id or "default_user",
                message=payload.message,
                conversation_id=payload.conversation_id
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
    except (LLMError, RepositoryError, ApplicationException, InfrastructureException) as e:
        # Errors before streaming starts
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

