"""Chat streaming API routes (SSE)."""
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import StreamingResponse
from app.api.dto.chat_dto import MessageRequestDTO
from app.api.dependencies import (
    get_stream_message_use_case,
    get_authenticated_user_id,
    check_rate_limit
)
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
        # Track conversation_id - it will be set when conversation is saved
        final_conversation_id = conversation_id
        
        # Stream chunks from use case
        async for chunk in use_case.execute(
            user_id=user_id,
            message_content=message,
            conversation_id=conversation_id
        ):
            # Check if this chunk contains conversation_id metadata
            if isinstance(chunk, str) and chunk.startswith("__CONVERSATION_ID__:"):
                final_conversation_id = chunk.replace("__CONVERSATION_ID__:", "")
                # Send conversation_id as metadata event
                metadata = json.dumps({"conversation_id": final_conversation_id})
                yield f"data: {metadata}\n\n"
                continue
            
            # Format as SSE (Server-Sent Events)
            data = json.dumps({"chunk": chunk})
            yield f"data: {data}\n\n"
        
        # Send completion event with conversation_id
        completion_data = {"done": True}
        if final_conversation_id:
            completion_data["conversation_id"] = final_conversation_id
        
        # Send completion event
        yield f"data: {json.dumps(completion_data)}\n\n"
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
    # Dependencies are resolved in order: FastAPI ensures get_authenticated_user_id
    # executes before check_rate_limit, which depends on user_id
    user_id: str = Depends(get_authenticated_user_id),  # 1. Authenticate first
    _: None = Depends(check_rate_limit),  # 2. Then rate limit (depends on user_id)
    use_case: StreamMessageUseCase = Depends(get_stream_message_use_case)  # 3. Finally use case
):
    """
    Stream AI response using Server-Sent Events (SSE).
    
    This endpoint requires authentication via JWT token in the Authorization header.
    The user ID is automatically extracted from the token - it should NOT be provided
    in the request body.
    
    This endpoint:
    - Saves user message immediately
    - Streams LLM response in real-time
    - Saves assistant message when complete
    
    This ensures data persistence while providing streaming UX.
    
    Args:
        payload: The message request DTO (without user_id).
        request: FastAPI request for correlation ID.
        user_id: Authenticated user ID extracted from JWT token (injected via dependency).
        use_case: Injected StreamMessageUseCase.
        
    Returns:
        StreamingResponse with SSE-formatted chunks.
        
    Raises:
        HTTPException: If authentication fails or use case setup fails (before streaming starts).
    """
    try:
        return StreamingResponse(
            _format_sse_stream(
                use_case=use_case,
                user_id=user_id,
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

