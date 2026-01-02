"""Fake implementations of domain ports for unit testing.

These fakes implement the domain ports (Protocols) and are used in unit tests
to ensure the application layer depends only on domain ports, not concrete implementations.
"""
from typing import Optional, List, Dict
from app.domain.ports.llm_port import LLMPort
from app.domain.ports.repository_port import RepositoryPort
from app.domain.entities.conversation import Conversation
from app.domain.value_objects.message import Message


class FakeLLM(LLMPort):
    """
    Fake LLM implementation for unit testing.
    
    This fake implements LLMPort and can be used to test use cases
    without depending on infrastructure implementations.
    """
    
    def __init__(self, response: str = "ok", should_raise: Optional[Exception] = None):
        """
        Initialize fake LLM.
        
        Args:
            response: The response to return when generate is called.
            should_raise: Optional exception to raise when generate is called.
        """
        self.response = response
        self.should_raise = should_raise
        self.called_with: Optional[str] = None
        self.call_count = 0
    
    async def generate(self, message: str) -> str:
        """
        Generate a fake response.
        
        Args:
            message: The input message (stored for verification).
            
        Returns:
            The configured fake response.
            
        Raises:
            The configured exception if should_raise is set.
        """
        self.called_with = message
        self.call_count += 1
        
        if self.should_raise:
            raise self.should_raise
        
        return self.response


class FakeRepository(RepositoryPort):
    """
    Fake repository implementation for unit testing.
    
    This fake implements RepositoryPort and stores conversations in memory
    for testing purposes without depending on infrastructure implementations.
    """
    
    def __init__(self):
        """Initialize fake repository with empty storage."""
        self._storage: Dict[str, Conversation] = {}
        self.save_count = 0
        self.find_by_id_count = 0
        self.find_by_user_id_count = 0
        self.delete_count = 0
    
    async def save(self, conversation: Conversation) -> Conversation:
        """
        Save a conversation in memory.
        
        Args:
            conversation: The conversation to save.
            
        Returns:
            The saved conversation (with ID if not set).
        """
        self.save_count += 1
        
        # Generate ID if not set
        if conversation.id is None:
            import uuid
            conversation.id = str(uuid.uuid4())
        
        self._storage[conversation.id] = conversation
        return conversation
    
    async def find_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """
        Find a conversation by ID.
        
        Args:
            conversation_id: The conversation ID.
            
        Returns:
            The conversation if found, None otherwise.
        """
        self.find_by_id_count += 1
        return self._storage.get(conversation_id)
    
    async def find_by_user_id(self, user_id: str) -> List[Conversation]:
        """
        Find all conversations for a user.
        
        Args:
            user_id: The user ID.
            
        Returns:
            List of conversations for the user.
        """
        self.find_by_user_id_count += 1
        return [
            conv for conv in self._storage.values()
            if conv.user_id == user_id
        ]
    
    async def delete(self, conversation_id: str) -> bool:
        """
        Delete a conversation by ID.
        
        Args:
            conversation_id: The conversation ID.
            
        Returns:
            True if deleted, False if not found.
        """
        self.delete_count += 1
        
        if conversation_id in self._storage:
            del self._storage[conversation_id]
            return True
        return False

