"""Use case for streaming message processing.

This use case handles streaming responses while maintaining data persistence
and following Clean Architecture principles.
"""
from typing import Optional, AsyncGenerator
from io import StringIO
from app.domain.ports.llm_port import LLMPort
from app.domain.ports.repository_port import RepositoryPort
from app.domain.ports.logger_port import LoggerPort
from app.domain.value_objects.message import Message
from app.domain.entities.conversation import Conversation
from app.domain.exceptions import LLMError, RepositoryError

# Maximum response length to prevent excessive costs and memory usage
MAX_RESPONSE_CHARS = 4000  # Adjust based on cost and model limitations


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
                # If conversation_id provided but not found, create a new one
                # This allows frontend to work even if conversation wasn't created via API first
                if self.logger:
                    self.logger.info(
                        "Conversation ID provided but not found, creating new conversation",
                        provided_conversation_id=conversation_id,
                        user_id=user_id
                    )
                conversation = Conversation(user_id=user_id)
                # Note: The conversation will get a new ID when saved, ignoring the provided one
            else:
                # SECURITY: Verify that the conversation belongs to the authenticated user
                if conversation.user_id != user_id:
                    if self.logger:
                        self.logger.warning(
                            "Access denied: conversation belongs to different user",
                            conversation_id=conversation_id,
                            conversation_user_id=conversation.user_id,
                            authenticated_user_id=user_id
                        )
                    raise RepositoryError(
                        f"Conversation {conversation_id} does not belong to user {user_id}"
                    )
        else:
            conversation = Conversation(user_id=user_id)
        
        # 2. Create and save user message immediately
        user_message = Message(content=message_content, role="user")
        conversation.add_message(user_message)
        saved_conversation = await self.repository.save(conversation)
        
        # Yield conversation_id as metadata before streaming chunks
        # Frontend can extract this to track the conversation
        yield f"__CONVERSATION_ID__:{saved_conversation.id}"
        
        if self.logger:
            self.logger.debug(
                "User message saved before streaming",
                conversation_id=saved_conversation.id
            )
        
        # 3. Stream LLM response and accumulate chunks using StringIO for efficiency
        response_buffer = StringIO()
        streaming_failed = False
        error_message = None
        response_truncated = False
        current_length = 0
        
        try:
            if self.logger:
                self.logger.debug("Starting LLM stream generation")
            
            chunk_count = 0
            async for chunk in self.llm.generate_stream(message_content):
                if chunk:  # Only process non-empty chunks
                    chunk_length = len(chunk)
                    current_length += chunk_length
                    
                    # Check if we've exceeded the maximum response length
                    if current_length > MAX_RESPONSE_CHARS:
                        if self.logger:
                            self.logger.warning(
                                "Response length exceeded maximum, truncating",
                                max_chars=MAX_RESPONSE_CHARS,
                                current_length=current_length,
                                conversation_id=saved_conversation.id
                            )
                        response_truncated = True
                        # Yield remaining characters up to limit
                        remaining = MAX_RESPONSE_CHARS - (current_length - chunk_length)
                        if remaining > 0:
                            truncated_chunk = chunk[:remaining]
                            response_buffer.write(truncated_chunk)
                            chunk_count += 1
                            yield truncated_chunk
                        break
                    
                    response_buffer.write(chunk)
                    chunk_count += 1
                    yield chunk  # Yield chunk to API layer immediately
            
            if self.logger:
                if chunk_count == 0:
                    self.logger.warning(
                        "Streaming completed but no chunks received",
                        conversation_id=saved_conversation.id
                    )
                else:
                    self.logger.debug(
                        "LLM stream completed",
                        total_chunks=chunk_count,
                        total_length=current_length,
                        truncated=response_truncated,
                        conversation_id=saved_conversation.id
                    )
        except Exception as e:
            streaming_failed = True
            error_message = str(e)
            
            if self.logger:
                self.logger.error(
                    "LLM streaming failed during generation",
                    error=error_message,
                    error_type=type(e).__name__,
                    chunks_received=chunk_count,
                    conversation_id=saved_conversation.id
                )
            
            # Save error state to conversation
            try:
                error_msg = Message(
                    content=f"[Erro ao gerar resposta: {error_message}]",
                    role="assistant"
                )
                conversation.add_message(error_msg)
                await self.repository.save(conversation)
                
                if self.logger:
                    self.logger.info(
                        "Error state saved to conversation",
                        conversation_id=conversation.id
                    )
            except Exception as save_error:
                # If we can't save the error, log it but don't fail silently
                if self.logger:
                    self.logger.error(
                        "Failed to save error state to conversation",
                        error=str(save_error),
                        original_error=error_message
                    )
            
            # Re-raise the original exception
            raise LLMError(f"Failed to generate streaming LLM response: {error_message}") from e
        
        # 4. Create and save assistant message with full response
        # Only save if streaming completed successfully
        if not streaming_failed and chunk_count > 0:
            full_response = response_buffer.getvalue()
            
            # Add truncation notice if response was truncated
            if response_truncated:
                full_response += "\n\n[Resposta truncada devido ao limite de tamanho]"
            
            assistant_message = Message(content=full_response, role="assistant")
            conversation.add_message(assistant_message)
            
            final_conversation = await self.repository.save(conversation)
            
            if self.logger:
                self.logger.info(
                    "Streaming message processed successfully",
                    conversation_id=final_conversation.id,
                    user_id=user_id,
                    messages_count=len(final_conversation.messages),
                    response_length=len(full_response),
                    truncated=response_truncated
                )
        elif not streaming_failed:
            # Edge case: streaming completed but no chunks received
            if self.logger:
                self.logger.warning(
                    "Streaming completed but no chunks received",
                    conversation_id=saved_conversation.id
                )

