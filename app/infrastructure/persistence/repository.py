"""Repository implementation for persistence."""
from typing import Optional, List
from datetime import datetime
import uuid
from app.domain.entities.conversation import Conversation
from app.domain.ports.repository_port import RepositoryPort
from app.domain.exceptions import RepositoryError
from app.domain.value_objects.message import Message
from app.infrastructure.persistence.models import ConversationModel, Base


class InMemoryRepository(RepositoryPort):
    """
    In-memory repository implementation for development and testing.
    
    In production, this should be replaced with a database-backed implementation.
    """
    
    def __init__(self):
        """Initialize the in-memory repository."""
        self._storage: dict[str, ConversationModel] = {}
    
    async def save(self, conversation: Conversation) -> Conversation:
        """
        Save a conversation.
        
        Args:
            conversation: The conversation entity to save.
            
        Returns:
            The saved conversation with generated ID if applicable.
        """
        try:
            # Convert entity to model
            if conversation.id is None:
                conversation.id = str(uuid.uuid4())
            
            # Convert messages to dict format
            messages_data = [
                {
                    "content": msg.content,
                    "role": msg.role,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                }
                for msg in conversation.messages
            ]
            
            model = ConversationModel(
                id=conversation.id,
                user_id=conversation.user_id,
                messages=messages_data,
                created_at=conversation.created_at or datetime.now(),
                updated_at=conversation.updated_at or datetime.now()
            )
            
            self._storage[conversation.id] = model
            
            # Update conversation timestamps
            conversation.updated_at = datetime.now()
            if conversation.created_at is None:
                conversation.created_at = datetime.now()
            
            return conversation
        except Exception as e:
            raise RepositoryError(f"Failed to save conversation: {str(e)}") from e
    
    async def find_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """
        Find a conversation by ID.
        
        Args:
            conversation_id: The unique identifier of the conversation.
            
        Returns:
            The conversation if found, None otherwise.
        """
        try:
            model = self._storage.get(conversation_id)
            if model is None:
                return None
            
            return self._model_to_entity(model)
        except Exception as e:
            raise RepositoryError(f"Failed to find conversation: {str(e)}") from e
    
    async def find_by_user_id(self, user_id: str) -> List[Conversation]:
        """
        Find all conversations for a user.
        
        Args:
            user_id: The user identifier.
            
        Returns:
            List of conversations for the user.
        """
        try:
            models = [
                model for model in self._storage.values()
                if model.user_id == user_id
            ]
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to find conversations: {str(e)}") from e
    
    async def delete(self, conversation_id: str) -> bool:
        """
        Delete a conversation by ID.
        
        Args:
            conversation_id: The unique identifier of the conversation.
            
        Returns:
            True if deleted, False if not found.
        """
        try:
            if conversation_id in self._storage:
                del self._storage[conversation_id]
                return True
            return False
        except Exception as e:
            raise RepositoryError(f"Failed to delete conversation: {str(e)}") from e
    
    def _model_to_entity(self, model: ConversationModel) -> Conversation:
        """Convert a model to an entity."""
        # Convert messages from dict to Message value objects
        messages = [
            Message(
                content=msg_data["content"],
                role=msg_data["role"],
                timestamp=datetime.fromisoformat(msg_data["timestamp"])
                if msg_data.get("timestamp") else None
            )
            for msg_data in model.messages
        ]
        
        conversation = Conversation(
            user_id=model.user_id,
            id=model.id,
            messages=messages,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
        
        return conversation

