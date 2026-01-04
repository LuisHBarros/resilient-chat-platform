"""Repository port for persistence operations."""
from typing import Protocol, Optional, List
from app.domain.entities.conversation import Conversation


class RepositoryPort(Protocol):
    """
    Protocol defining the interface for conversation persistence.
    
    This port follows the Hexagonal Architecture pattern, allowing the domain
    and application layers to remain independent of specific database implementations.
    """
    
    async def save(self, conversation: Conversation) -> Conversation:
        """
        Save a conversation.
        
        Args:
            conversation: The conversation entity to save.
            
        Returns:
            The saved conversation with generated ID if applicable.
            
        Raises:
            RepositoryError: If the save operation fails.
        """
        ...
    
    async def find_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """
        Find a conversation by ID.
        
        Args:
            conversation_id: The unique identifier of the conversation.
            
        Returns:
            The conversation if found, None otherwise.
            
        Raises:
            RepositoryError: If the query operation fails.
        """
        ...
    
    async def find_by_user_id(self, user_id: str) -> List[Conversation]:
        """
        Find all conversations for a user.
        
        Args:
            user_id: The user identifier.
            
        Returns:
            List of conversations for the user.
            
        Raises:
            RepositoryError: If the query operation fails.
        """
        ...
    
    async def delete(self, conversation_id: str) -> bool:
        """
        Delete a conversation by ID.
        
        Args:
            conversation_id: The unique identifier of the conversation.
            
        Returns:
            True if deleted, False if not found.
            
        Raises:
            RepositoryError: If the delete operation fails.
        """
        ...
    
    async def check_health(self) -> bool:
        """
        Check repository health/connectivity.
        
        This method verifies that the repository can connect to its underlying
        storage (database, cache, etc.). Used for health checks and readiness probes.
        
        Returns:
            True if repository is healthy and can connect, False otherwise.
            
        Raises:
            RepositoryError: If health check fails unexpectedly.
        """
        ...

