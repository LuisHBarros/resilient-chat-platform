"""Contract tests for LLMPort implementations.

These tests verify that all LLM implementations correctly implement
the LLMPort protocol. This ensures that any implementation can be
used interchangeably.
"""
import pytest
from app.domain.ports.llm_port import LLMPort
from app.infrastructure.llm import OpenAIProvider, BedrockProvider, MockProvider
from tests.unit.fakes import FakeLLM


class TestLLMPortContract:
    """Contract tests for LLMPort implementations."""
    
    @pytest.mark.parametrize("llm_class", [
        FakeLLM,
        MockProvider,
        # Note: OpenAIProvider and BedrockProvider require API keys,
        # so they're tested in integration tests
    ])
    @pytest.mark.asyncio
    async def test_llm_implements_port(self, llm_class):
        """Test that LLM implementation implements LLMPort protocol."""
        # Create instance
        if llm_class == FakeLLM:
            llm = llm_class(response="test")
        else:
            llm = llm_class()
        
        # Verify it implements the protocol
        assert isinstance(llm, LLMPort)
        
        # Verify it has the required method
        assert hasattr(llm, "generate")
        assert callable(getattr(llm, "generate"))
    
    @pytest.mark.parametrize("llm_class", [
        FakeLLM,
        MockProvider,
    ])
    @pytest.mark.asyncio
    async def test_generate_returns_string(self, llm_class):
        """Test that generate method returns a string."""
        if llm_class == FakeLLM:
            llm = llm_class(response="test response")
        else:
            llm = llm_class()
        
        result = await llm.generate("test message")
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    @pytest.mark.parametrize("llm_class", [
        FakeLLM,
        MockProvider,
    ])
    @pytest.mark.asyncio
    async def test_generate_accepts_string(self, llm_class):
        """Test that generate method accepts string input."""
        if llm_class == FakeLLM:
            llm = llm_class(response="ok")
        else:
            llm = llm_class()
        
        # Should not raise TypeError
        result = await llm.generate("test")
        assert isinstance(result, str)

