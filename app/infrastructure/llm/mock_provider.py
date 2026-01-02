"""Mock LLM provider implementation for testing and development."""
from app.domain.ports.llm_port import LLMPort


class MockProvider(LLMPort):
    """
    Mock LLM implementation that echoes the input message.
    
    Useful for:
    - Local development
    - Testing
    - CI/CD pipelines where real LLM APIs are not available
    """
    
    async def generate(self, message: str) -> str:
        """
        Generate a mock response by echoing the input message.
        
        Args:
            message: The input message.
            
        Returns:
            A formatted echo response.
        """
        return f"Echo: {message}"

