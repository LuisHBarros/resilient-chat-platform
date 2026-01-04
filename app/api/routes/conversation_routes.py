"""Conversation history API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.api.dependencies import (
    get_repository,
    get_authenticated_user_id
)
from app.domain.ports.repository_port import RepositoryPort
from app.domain.exceptions import RepositoryError
from pydantic import BaseModel
from datetime import datetime


router = APIRouter(prefix="/conversations", tags=["conversations"])


class MessageDTO(BaseModel):
    """Message data transfer object."""
    content: str
    role: str
    timestamp: datetime


class ConversationDTO(BaseModel):
    """Conversation data transfer object."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageDTO]


class ConversationSummaryDTO(BaseModel):
    """Conversation summary without messages."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    last_message_preview: str


@router.get("", response_model=List[ConversationSummaryDTO])
async def get_user_conversations(
    user_id: str = Depends(get_authenticated_user_id),
    repository: RepositoryPort = Depends(get_repository)
):
    """
    Get all conversations for the authenticated user.
    
    This endpoint returns a list of conversation summaries without full message history.
    Use GET /conversations/{conversation_id} to get full conversation details.
    
    Args:
        user_id: Authenticated user ID extracted from JWT token (injected via dependency).
        repository: Injected repository instance.
        
    Returns:
        List of conversation summaries ordered by updated_at (most recent first).
        
    Raises:
        HTTPException: If repository operation fails.
    """
    try:
        conversations = await repository.find_by_user_id(user_id)
        
        # Convert to DTOs with summaries
        summaries = []
        for conv in conversations:
            message_count = len(conv.messages)
            last_message = ""
            
            if conv.messages:
                last_msg = conv.messages[-1]
                # Get preview of last message (first 100 chars)
                last_message = last_msg.content[:100] + "..." if len(last_msg.content) > 100 else last_msg.content
            
            summaries.append(ConversationSummaryDTO(
                id=conv.id,
                user_id=conv.user_id,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=message_count,
                last_message_preview=last_message
            ))
        
        return summaries
        
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversations: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/{conversation_id}", response_model=ConversationDTO)
async def get_conversation_by_id(
    conversation_id: str,
    user_id: str = Depends(get_authenticated_user_id),
    repository: RepositoryPort = Depends(get_repository)
):
    """
    Get a specific conversation with full message history.
    
    This endpoint returns the complete conversation including all messages.
    The conversation must belong to the authenticated user.
    
    Args:
        conversation_id: The conversation ID to retrieve.
        user_id: Authenticated user ID extracted from JWT token (injected via dependency).
        repository: Injected repository instance.
        
    Returns:
        Complete conversation with all messages.
        
    Raises:
        HTTPException: If conversation not found or doesn't belong to user.
    """
    try:
        conversation = await repository.find_by_id(conversation_id)
        
        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        # Verify the conversation belongs to the authenticated user
        if conversation.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this conversation"
            )
        
        # Convert to DTO
        messages = [
            MessageDTO(
                content=msg.content,
                role=msg.role,
                timestamp=msg.timestamp
            )
            for msg in conversation.messages
        ]
        
        return ConversationDTO(
            id=conversation.id,
            user_id=conversation.user_id,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=messages
        )
        
    except HTTPException:
        raise
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversation: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user_id: str = Depends(get_authenticated_user_id),
    repository: RepositoryPort = Depends(get_repository)
):
    """
    Delete a conversation and all its messages.
    
    This operation is permanent and cannot be undone.
    The conversation must belong to the authenticated user.
    
    Args:
        conversation_id: The conversation ID to delete.
        user_id: Authenticated user ID extracted from JWT token (injected via dependency).
        repository: Injected repository instance.
        
    Returns:
        Success message.
        
    Raises:
        HTTPException: If conversation not found or doesn't belong to user.
    """
    try:
        # First verify the conversation exists and belongs to the user
        conversation = await repository.find_by_id(conversation_id)
        
        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        if conversation.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this conversation"
            )
        
        # Delete the conversation
        deleted = await repository.delete(conversation_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        return {"message": "Conversation deleted successfully", "conversation_id": conversation_id}
        
    except HTTPException:
        raise
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

