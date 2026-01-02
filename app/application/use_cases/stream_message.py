"""Use case for streaming message processing.

This use case handles streaming responses while maintaining data persistence
and following Clean Architecture principles.
"""
from typing import Optional, AsyncGenerator
from app.domain.ports.llm_port import LLMPort
from app.domain.ports.repository_port import RepositoryPort
from app.domain.ports.logger_port import LoggerPort
from app.domain.value_objects.message import Message
from app.domain.entities.conversation import Conversation
from app.domain.exceptions import LLMError, RepositoryError


class StreamMessageUseCase:
    """
    Use case for processing a message with streaming response.
    
    This use case:
    1. Loads or creates conversation
    2. Saves user message
    3. Streams LLM response chunks
    4. Accumulates full response
    5. Saves assistant message
    
    Business Rules:
    - User message is saved before streaming starts
    - Assistant response is saved after streaming completes
    - Conversation history is preserved
    - If conversation_id is provided, it must exist
    """
    
    def __init__(
        self,
        llm: LLMPort,
        repository: RepositoryPort,
        logger: Optional[LoggerPort] = None
    ):
        """
        Initialize the streaming use case.
        
        Args:
            llm: LLM port for generating streaming responses.
            repository: Repository port for persistence.
            logger: Optional logger port for observability.
        """
        self.llm = llm
        self.repository = repository
        self.logger = logger
    
    async def execute(
        self,
        user_id: str,
        message_content: str,
        conversation_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Execute the streaming use case.
        
        This method:
        1. Loads or creates conversation
        2. Saves user message immediately
        3. Streams LLM response chunks (yields them)
        4. Accumulates full response
        5. Saves assistant message when complete
        
        Args:
            user_id: The user identifier.
            message_content: The message content from the user.
            conversation_id: Optional conversation ID to continue existing conversation.
            
        Yields:
            Chunks of the LLM response as they become available.
            
        Raises:
            LLMError: If LLM generation fails.
            RepositoryError: If repository operations fail.
        """
        # Log start of processing
        if self.logger:
            self.logger.info(
                "Processing streaming message",
                user_id=user_id,
                conversation_id=conversation_id,
                message_length=len(message_content)
            )
        
        # 1. Load or create conversation
        if conversation_id:
            conversation = await self.repository.find_by_id(conversation_id)
            if conversation is None:
                if self.logger:
                    self.logger.warning(
                        "Conversation not found for streaming",
                        conversation_id=conversation_id,
                        user_id=user_id
                    )
                raise RepositoryError(f"Conversation {conversation_id} not found")
        else:
            conversation = Conversation(user_id=user_id)
        
        # 2. Create and save user message immediately
        user_message = Message(content=message_content, role="user")
        conversation.add_message(user_message)
        saved_conversation = await self.repository.save(conversation)
        
        if self.logger:
            self.logger.debug(
                "User message saved before streaming",
                conversation_id=saved_conversation.id
            )
        
        # 3. Stream LLM response and accumulate chunks
        full_response_chunks = []
        
        try:
            if self.logger:
                self.logger.debug("Starting LLM stream generation")
            
            async for chunk in self.llm.generate_stream(message_content):
                full_response_chunks.append(chunk)
                yield chunk  # Yield chunk to API layer immediately
            
            if self.logger:
                self.logger.debug(
                    "LLM stream completed",
                    total_chunks=len(full_response_chunks)
                )
        except Exception as e:
            if self.logger:
                self.logger.error(
                    "LLM streaming failed",
                    error=str(e),
                    error_type=type(e).__name__
                )
            raise LLMError(f"Failed to generate streaming LLM response: {str(e)}") from e
        
        # 4. Create and save assistant message with full response
        full_response = "".join(full_response_chunks)
        assistant_message = Message(content=full_response, role="assistant")
        conversation.add_message(assistant_message)
        
        final_conversation = await self.repository.save(conversation)
        
        if self.logger:
            self.logger.info(
                "Streaming message processed successfully",
                conversation_id=final_conversation.id,
                user_id=user_id,
                messages_count=len(final_conversation.messages),
                response_length=len(full_response)
            )

