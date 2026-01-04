"""Use case for processing a message."""
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.ports.logger_port import LoggerPort

from app.domain.ports.llm_port import LLMPort
from app.domain.ports.repository_port import RepositoryPort
from app.domain.value_objects.message import Message
from app.domain.entities.conversation import Conversation
from app.domain.exceptions import LLMError, RepositoryError

# OpenTelemetry tracing
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer(__name__)


class ProcessMessageUseCase:
    """
    Use case for processing a user message and generating a response.
    
    This use case orchestrates:
    1. Loading conversation history
    2. Generating LLM response
    3. Saving the conversation
    
    Business Rules:
    - A conversation must belong to a user (user_id is required)
    - Messages must be non-empty strings
    - Conversation history is preserved across messages
    - Each message exchange generates a user message and an assistant response
    - If conversation_id is provided, it must exist in the repository
    - The conversation is automatically saved after processing
    """
    
    def __init__(
        self,
        llm: LLMPort,
        repository: RepositoryPort,
        logger: Optional["LoggerPort"] = None
    ):
        """
        Initialize the use case.
        
        Args:
            llm: LLM port for generating responses.
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
    ) -> dict:
        """
        Execute the use case.
        
        Args:
            user_id: The user identifier.
            message_content: The message content from the user.
            conversation_id: Optional conversation ID to continue existing conversation.
            
        Returns:
            Dictionary containing:
            - conversation_id: The conversation identifier
            - response: The generated response
            - user_message: The user's message
            - assistant_message: The assistant's response
            
        Raises:
            LLMError: If LLM generation fails.
            RepositoryError: If repository operations fail.
        """
        # Start tracing span for the entire use case
        with tracer.start_as_current_span("ProcessMessageUseCase.execute") as span:
            # Add attributes to span
            span.set_attribute("user_id", user_id)
            span.set_attribute("message_length", len(message_content))
            if conversation_id:
                span.set_attribute("conversation_id", conversation_id)
            
            # Log start of processing
            if self.logger:
                self.logger.info(
                    "Processing message",
                    user_id=user_id,
                    conversation_id=conversation_id,
                    message_length=len(message_content)
                )
            
            # Load or create conversation (with tracing)
            with tracer.start_as_current_span("repository.find_or_create_conversation") as repo_span:
                if conversation_id:
                    conversation = await self.repository.find_by_id(conversation_id)
                    if conversation is None:
                        # If conversation_id provided but not found, create a new one
                        # This allows frontend to work even if conversation wasn't created via API first
                        repo_span.set_attribute("action", "create_new")
                        if self.logger:
                            self.logger.info(
                                "Conversation ID provided but not found, creating new conversation",
                                provided_conversation_id=conversation_id,
                                user_id=user_id
                            )
                        conversation = Conversation(user_id=user_id)
                        # Note: The conversation will get a new ID when saved, ignoring the provided one
                    else:
                        repo_span.set_attribute("action", "found_existing")
                else:
                    repo_span.set_attribute("action", "create_new")
                    conversation = Conversation(user_id=user_id)
            
            # Create user message value object
            user_message = Message(content=message_content, role="user")
            conversation.add_message(user_message)
            
            # Generate response using LLM (with tracing)
            with tracer.start_as_current_span("llm.generate") as llm_span:
                llm_span.set_attribute("llm.provider", type(self.llm).__name__)
                try:
                    if self.logger:
                        self.logger.debug("Calling LLM to generate response")
                    response_content = await self.llm.generate(message_content)
                    llm_span.set_attribute("llm.response_length", len(response_content))
                    if self.logger:
                        self.logger.debug(
                            "LLM response generated",
                            response_length=len(response_content)
                        )
                except Exception as e:
                    llm_span.record_exception(e)
                    llm_span.set_status(Status(StatusCode.ERROR, str(e)))
                    if self.logger:
                        self.logger.error(
                            "LLM generation failed",
                            error=str(e),
                            error_type=type(e).__name__
                        )
                    raise LLMError(f"Failed to generate LLM response: {str(e)}") from e
            
            # Create assistant message value object
            assistant_message = Message(content=response_content, role="assistant")
            conversation.add_message(assistant_message)
            
            # Save conversation (with tracing)
            with tracer.start_as_current_span("repository.save_conversation") as save_span:
                saved_conversation = await self.repository.save(conversation)
                save_span.set_attribute("conversation.id", saved_conversation.id)
                save_span.set_attribute("conversation.messages_count", len(saved_conversation.messages))
        
        # Log successful completion
        if self.logger:
            self.logger.info(
                "Message processed successfully",
                conversation_id=saved_conversation.id,
                user_id=user_id,
                messages_count=len(saved_conversation.messages)
            )
        
        return {
            "conversation_id": saved_conversation.id,
            "response": response_content,
            "user_message": message_content,
            "assistant_message": response_content
        }

