"""Data Transfer Objects for chat API.

DTOs are used to transfer data between the API layer and external clients.
They provide:
- Input validation
- API contract definition
- Serialization/deserialization
- Documentation (via OpenAPI/Swagger)
"""
from pydantic import BaseModel, Field, validator
from typing import Optional


class MessageRequestDTO(BaseModel):
    """
    DTO for message request.
    
    This DTO validates and structures incoming message requests from clients.
    
    Note: user_id is no longer accepted in the request body. It is automatically
    extracted from the JWT token in the Authorization header.
    """
    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="The message content (1-10000 characters)"
    )
    conversation_id: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Conversation ID to continue existing conversation (optional)"
    )
    model_id: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Optional model ID to override default model (e.g., 'gpt-4', 'claude-3-opus')"
    )
    
    @validator("message")
    def validate_message_not_empty(cls, v):
        """Validate that message is not just whitespace."""
        if not v or not v.strip():
            raise ValueError("Message cannot be empty or only whitespace")
        return v.strip()
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "message": "Hello, how are you?",
                "conversation_id": "conv-456",
                "model_id": "gpt-4"
            }
        }


class MessageResponseDTO(BaseModel):
    """
    DTO for message response.
    
    This DTO structures the response sent back to clients after processing a message.
    """
    conversation_id: str = Field(
        ...,
        description="The conversation identifier (UUID format)"
    )
    response: str = Field(
        ...,
        description="The generated AI response"
    )
    user_message: str = Field(
        ...,
        description="The user's original message"
    )
    assistant_message: str = Field(
        ...,
        description="The assistant's response (same as response field)"
    )
    
    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                "response": "I'm doing well, thank you! How can I help you today?",
                "user_message": "Hello, how are you?",
                "assistant_message": "I'm doing well, thank you! How can I help you today?"
            }
        }

