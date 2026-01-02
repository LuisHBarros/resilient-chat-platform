"""Legacy tests - kept for backward compatibility.

These tests use infrastructure implementations. For new tests,
use test_process_message_use_case.py with fakes instead.
"""
import pytest
from app.application.use_cases.process_message import ProcessMessageUseCase
from app.infrastructure.persistence import InMemoryRepository
from tests.unit.fakes import FakeLLM


class TestProcessMessageUseCaseLegacy:
    """Legacy unit tests using infrastructure implementations."""

    @pytest.mark.asyncio
    async def test_execute_calls_llm_generate(self):
        """Test that execute method calls LLM generate with correct message."""
        fake_llm = FakeLLM(response="Test response")
        repository = InMemoryRepository()
        use_case = ProcessMessageUseCase(llm=fake_llm, repository=repository)
        
        result = await use_case.execute(
            user_id="test_user",
            message_content="Test message"
        )
        
        assert result["response"] == "Test response"
        assert fake_llm.called_with == "Test message"
        assert "conversation_id" in result

    @pytest.mark.asyncio
    async def test_execute_preserves_llm_response(self):
        """Test that execute method preserves the exact LLM response."""
        custom_response = "Custom LLM response with special chars: @#$%"
        fake_llm = FakeLLM(response=custom_response)
        repository = InMemoryRepository()
        use_case = ProcessMessageUseCase(llm=fake_llm, repository=repository)
        
        result = await use_case.execute(
            user_id="test_user",
            message_content="Any message"
        )
        
        assert result["response"] == custom_response

    @pytest.mark.asyncio
    async def test_execute_with_conversation_id(self):
        """Test that execute method works with conversation ID."""
        fake_llm = FakeLLM(response="Response")
        repository = InMemoryRepository()
        use_case = ProcessMessageUseCase(llm=fake_llm, repository=repository)
        
        # First message
        result1 = await use_case.execute(
            user_id="user1",
            message_content="Message 1"
        )
        conversation_id = result1["conversation_id"]
        
        # Continue conversation
        result2 = await use_case.execute(
            user_id="user1",
            message_content="Message 2",
            conversation_id=conversation_id
        )
        
        assert result2["conversation_id"] == conversation_id

