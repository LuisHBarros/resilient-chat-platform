"""AWS Bedrock LLM provider implementation."""
import json
import os
import asyncio
from typing import Optional, AsyncGenerator
from app.domain.ports.llm_port import LLMPort


class BedrockProvider(LLMPort):
    """
    AWS Bedrock LLM implementation.
    
    Requires AWS credentials configured (via AWS CLI, IAM role, or environment variables).
    """
    
    def __init__(
        self,
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        region: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ):
        """
        Initialize AWS Bedrock LLM client.
        
        Args:
            model_id: The Bedrock model ID to use.
            region: AWS region. If not provided, reads from AWS_REGION env var or uses 'us-east-1'.
            temperature: Sampling temperature (0.0 to 1.0).
            max_tokens: Maximum tokens in the response.
        """
        self.model_id = model_id
        self.region = region or os.getenv("AWS_REGION", "us-east-1")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = None
    
    def _get_client(self):
        """Lazy initialization of Bedrock runtime client."""
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client(
                    service_name="bedrock-runtime",
                    region_name=self.region
                )
            except ImportError:
                raise ImportError(
                    "boto3 package is required. Install it with: pip install boto3"
                )
        return self._client
    
    async def generate(self, message: str) -> str:
        """
        Generate a response using AWS Bedrock API.
        
        Args:
            message: The input message/prompt.
            
        Returns:
            The generated response from Bedrock.
            
        Raises:
            Exception: If API call fails (authentication, rate limit, etc.).
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        client = self._get_client()
        
        # Prepare the request body based on model type
        if "claude" in self.model_id.lower():
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": message
                    }
                ]
            })
        else:
            # Default format for other models
            body = json.dumps({
                "prompt": message,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            })
        
        try:
            # Bedrock uses synchronous boto3, so we use asyncio.to_thread
            response = await asyncio.to_thread(
                client.invoke_model,
                modelId=self.model_id,
                body=body,
                contentType="application/json",
                accept="application/json"
            )
            
            # Parse response based on model type
            response_body = json.loads(response["body"].read())
            
            if "claude" in self.model_id.lower():
                return response_body["content"][0]["text"]
            elif "amazon" in self.model_id.lower():
                return response_body["results"][0]["outputText"]
            else:
                # Generic fallback
                return str(response_body)
                
        except Exception as e:
            raise RuntimeError(f"AWS Bedrock API error: {str(e)}") from e
    
    async def generate_stream(self, message: str) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response using AWS Bedrock API with real streaming.
        
        Uses invoke_model_with_response_stream for true streaming (low TTFB).
        
        Args:
            message: The input message/prompt.
            
        Yields:
            Chunks of the generated response as they arrive from Bedrock.
            
        Raises:
            Exception: If API call fails.
        """
        client = self._get_client()
        
        # Prepare the request body based on model type
        if "claude" in self.model_id.lower():
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": message
                    }
                ]
            })
        else:
            # Default format for other models
            body = json.dumps({
                "prompt": message,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            })
        
        try:
            # Use invoke_model_with_response_stream for real streaming
            response = await asyncio.to_thread(
                client.invoke_model_with_response_stream,
                modelId=self.model_id,
                body=body,
                contentType="application/json",
                accept="application/json"
            )
            
            # Process streaming response
            stream = response.get('body')
            if stream:
                for event in stream:
                    # Note: boto3 stream iterator is synchronous, but we're running
                    # it in a thread, so this is acceptable for now
                    chunk = event.get('chunk')
                    if chunk:
                        chunk_bytes = chunk.get('bytes')
                        if chunk_bytes:
                            chunk_json = json.loads(chunk_bytes.decode())
                            
                            # Extract text based on model type
                            if "claude" in self.model_id.lower():
                                # Claude 3 format
                                if "delta" in chunk_json and "text" in chunk_json["delta"]:
                                    yield chunk_json["delta"]["text"]
                                elif "contentBlockDelta" in chunk_json:
                                    delta = chunk_json["contentBlockDelta"].get("delta", {})
                                    if "text" in delta:
                                        yield delta["text"]
                            elif "amazon" in self.model_id.lower():
                                # Amazon Titan format
                                if "outputText" in chunk_json:
                                    yield chunk_json["outputText"]
                            else:
                                # Generic fallback - try to extract any text field
                                if "text" in chunk_json:
                                    yield chunk_json["text"]
        except Exception as e:
            raise RuntimeError(f"AWS Bedrock streaming API error: {str(e)}") from e

