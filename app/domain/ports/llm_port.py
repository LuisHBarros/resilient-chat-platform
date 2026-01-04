from typing import Protocol, AsyncGenerator, Optional


class LLMPort(Protocol):
    """
    Protocol defining the interface for Large Language Model (LLM) implementations.
    
    This port follows the Hexagonal Architecture pattern, allowing the domain layer
    to remain independent of specific LLM provider implementations (OpenAI, etc.).
    
    Any class implementing this protocol must provide:
    - An async generate method that returns a complete response string
    - An async generate_stream method that yields response chunks (for streaming)
    """
    
    async def generate(self, message: str) -> str:
        """
        Generate a response from the LLM based on the input message.
        
        Args:
            message: The input message/prompt to send to the LLM.
            
        Returns:
            The generated response from the LLM as a string.
            
        Raises:
            Implementation-specific exceptions may be raised for errors such as:
            - API authentication failures
            - Rate limiting
            - Network errors
            - Invalid input
        """
        ...
    
    async def generate_stream(self, message: str) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response from the LLM.
        
        This method yields chunks of the response as they become available,
        allowing for real-time streaming to clients (e.g., via SSE).
        
        Args:
            message: The input message/prompt to send to the LLM.
            
        Yields:
            String chunks of the generated response.
            
        Raises:
            Implementation-specific exceptions may be raised for errors such as:
            - API authentication failures
            - Rate limiting
            - Network errors
            - Invalid input
        """
        ...