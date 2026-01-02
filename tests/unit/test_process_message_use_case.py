"""Unit tests for ProcessMessageUseCase using fakes.

These tests use fake implementations of domain ports to ensure:
1. The use case depends only on domain ports (not infrastructure)
2. Tests are fast and isolated
3. No external dependencies are required
"""
import pytest
from app.application.use_cases.process_message import ProcessMessageUseCase
from app.domain.exceptions import LLMError, RepositoryError
from tests.unit.fakes import FakeLLM, FakeRepository


class TestProcessMessageUseCase:
    """Unit tests for ProcessMessageUseCase using fakes."""

    @pytest.mark.asyncio
    async def test_execute_returns_llm_response(self):
        """Test that execute returns the LLM response."""
        fake_llm = FakeLLM(response="ok")
        fake_repo = FakeRepository()
        use_case = ProcessMessageUseCase(llm=fake_llm, repository=fake_repo)
        
        result = await use_case.execute(
            user_id="test_user",
            message_content="hi"
        )
        
        assert result["response"] == "ok"
        assert result["assistant_message"] == "ok"
        assert fake_llm.called_with == "hi"
        assert fake_llm.call_count == 1

    @pytest.mark.asyncio
    async def test_execute_saves_conversation(self):
        """Test that execute saves the conversation."""
        fake_llm = FakeLLM(response="response")
        fake_repo = FakeRepository()
        use_case = ProcessMessageUseCase(llm=fake_llm, repository=fake_repo)
        
        result = await use_case.execute(
            user_id="user1",
            message_content="message"
        )
        
        assert "conversation_id" in result
        assert result["conversation_id"] is not None
        assert fake_repo.save_count == 1
        
        # Verify conversation was saved
        saved = await fake_repo.find_by_id(result["conversation_id"])
        assert saved is not None
        assert saved.user_id == "user1"
        assert len(saved.messages) == 2  # user message + assistant response

    @pytest.mark.asyncio
    async def test_execute_continues_existing_conversation(self):
        """Test that execute continues an existing conversation."""
        fake_llm = FakeLLM(response="response")
        fake_repo = FakeRepository()
        use_case = ProcessMessageUseCase(llm=fake_llm, repository=fake_repo)
        
        # Create first conversation
        result1 = await use_case.execute(
            user_id="user1",
            message_content="first message"
        )
        conversation_id = result1["conversation_id"]
        
        # Continue conversation
        result2 = await use_case.execute(
            user_id="user1",
            message_content="second message",
            conversation_id=conversation_id
        )
        
        assert result2["conversation_id"] == conversation_id
        assert fake_repo.save_count == 2
        
        # Verify conversation has 4 messages (2 exchanges)
        saved = await fake_repo.find_by_id(conversation_id)
        assert len(saved.messages) == 4

    @pytest.mark.asyncio
    async def test_execute_raises_error_when_conversation_not_found(self):
        """Test that execute raises error when conversation_id doesn't exist."""
        fake_llm = FakeLLM(response="response")
        fake_repo = FakeRepository()
        use_case = ProcessMessageUseCase(llm=fake_llm, repository=fake_repo)
        
        with pytest.raises(RepositoryError, match="not found"):
            await use_case.execute(
                user_id="user1",
                message_content="message",
                conversation_id="non-existent-id"
            )

    @pytest.mark.asyncio
    async def test_execute_raises_llm_error_on_llm_failure(self):
        """Test that execute raises LLMError when LLM fails."""
        fake_llm = FakeLLM(should_raise=Exception("LLM API error"))
        fake_repo = FakeRepository()
        use_case = ProcessMessageUseCase(llm=fake_llm, repository=fake_repo)
        
        with pytest.raises(LLMError, match="Failed to generate LLM response"):
            await use_case.execute(
                user_id="user1",
                message_content="message"
            )

    @pytest.mark.asyncio
    async def test_execute_creates_user_and_assistant_messages(self):
        """Test that execute creates both user and assistant messages."""
        fake_llm = FakeLLM(response="assistant response")
        fake_repo = FakeRepository()
        use_case = ProcessMessageUseCase(llm=fake_llm, repository=fake_repo)
        
        result = await use_case.execute(
            user_id="user1",
            message_content="user message"
        )
        
        saved = await fake_repo.find_by_id(result["conversation_id"])
        assert len(saved.messages) == 2
        
        # First message is user message
        assert saved.messages[0].role == "user"
        assert saved.messages[0].content == "user message"
        
        # Second message is assistant response
        assert saved.messages[1].role == "assistant"
        assert saved.messages[1].content == "assistant response"

