"""Contract tests for RepositoryPort implementations.

These tests verify that all repository implementations correctly implement
the RepositoryPort protocol.
"""
import pytest
from app.domain.ports.repository_port import RepositoryPort
from app.domain.entities.conversation import Conversation
from app.domain.value_objects.message import Message
from app.infrastructure.persistence import InMemoryRepository
from tests.unit.fakes import FakeRepository


class TestRepositoryPortContract:
    """Contract tests for RepositoryPort implementations."""
    
    @pytest.mark.parametrize("repo_class", [
        FakeRepository,
        InMemoryRepository,
    ])
    def test_repository_implements_port(self, repo_class):
        """Test that repository implementation implements RepositoryPort protocol."""
        repo = repo_class()
        
        # Verify it implements the protocol
        assert isinstance(repo, RepositoryPort)
        
        # Verify it has all required methods
        assert hasattr(repo, "save")
        assert hasattr(repo, "find_by_id")
        assert hasattr(repo, "find_by_user_id")
        assert hasattr(repo, "delete")
    
    @pytest.mark.parametrize("repo_class", [
        FakeRepository,
        InMemoryRepository,
    ])
    @pytest.mark.asyncio
    async def test_save_returns_conversation(self, repo_class):
        """Test that save method returns a Conversation."""
        repo = repo_class()
        conversation = Conversation(user_id="test_user")
        
        result = await repo.save(conversation)
        
        assert isinstance(result, Conversation)
        assert result.id is not None
    
    @pytest.mark.parametrize("repo_class", [
        FakeRepository,
        InMemoryRepository,
    ])
    @pytest.mark.asyncio
    async def test_find_by_id_returns_optional_conversation(self, repo_class):
        """Test that find_by_id returns Optional[Conversation]."""
        repo = repo_class()
        
        # Test with non-existent ID
        result = await repo.find_by_id("non-existent")
        assert result is None
        
        # Test with existing ID
        conversation = Conversation(user_id="test_user")
        saved = await repo.save(conversation)
        result = await repo.find_by_id(saved.id)
        assert isinstance(result, Conversation)
        assert result.id == saved.id
    
    @pytest.mark.parametrize("repo_class", [
        FakeRepository,
        InMemoryRepository,
    ])
    @pytest.mark.asyncio
    async def test_find_by_user_id_returns_list(self, repo_class):
        """Test that find_by_user_id returns a list of conversations."""
        repo = repo_class()
        
        # Create conversations for different users
        conv1 = Conversation(user_id="user1")
        conv2 = Conversation(user_id="user1")
        conv3 = Conversation(user_id="user2")
        
        await repo.save(conv1)
        await repo.save(conv2)
        await repo.save(conv3)
        
        # Find by user_id
        result = await repo.find_by_user_id("user1")
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(c, Conversation) for c in result)
        assert all(c.user_id == "user1" for c in result)
    
    @pytest.mark.parametrize("repo_class", [
        FakeRepository,
        InMemoryRepository,
    ])
    @pytest.mark.asyncio
    async def test_delete_returns_bool(self, repo_class):
        """Test that delete returns a boolean."""
        repo = repo_class()
        
        # Test deleting non-existent
        result = await repo.delete("non-existent")
        assert isinstance(result, bool)
        assert result is False
        
        # Test deleting existing
        conversation = Conversation(user_id="test_user")
        saved = await repo.save(conversation)
        result = await repo.delete(saved.id)
        assert isinstance(result, bool)
        assert result is True
        
        # Verify it's deleted
        found = await repo.find_by_id(saved.id)
        assert found is None

