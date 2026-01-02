"""OpenAI LLM provider implementation."""
import os
from typing import Optional
from app.domain.ports.llm_port import LLMPort


class OpenAIProvider(LLMPort):
    """
    OpenAI LLM implementation using the OpenAI API.
    
    Requires OPENAI_API_KEY environment variable to be set.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 500
    ):
        """
        Initialize OpenAI LLM client.
        
        Args:
            api_key: OpenAI API key. If not provided, reads from OPENAI_API_KEY env var.
            model: The model to use (e.g., 'gpt-3.5-turbo', 'gpt-4').
            temperature: Sampling temperature (0.0 to 2.0).
            max_tokens: Maximum tokens in the response.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "openai package is required. Install it with: pip install openai"
                )
        return self._client
    
    async def generate(self, message: str) -> str:
        """
        Generate a response using OpenAI API.
        
        Args:
            message: The input message/prompt.
            
        Returns:
            The generated response from OpenAI.
            
        Raises:
            Exception: If API call fails (authentication, rate limit, etc.).
        """
        client = self._get_client()
        
        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": message}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content or ""
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}") from e

