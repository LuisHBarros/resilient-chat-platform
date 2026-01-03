"""OpenAI LLM provider implementation."""
import os
import time
from typing import Optional, AsyncGenerator, List
from app.domain.ports.llm_port import LLMPort
from app.infrastructure.config.settings import settings


class OpenAIProvider(LLMPort):
    """
    OpenAI LLM implementation using the OpenAI API.
    
    Requires OPENAI_API_KEY environment variable to be set.
    
    Supports both legacy models (gpt-3.5, gpt-4) using chat.completions API
    and newer models (gpt-5-*) using responses API.
    
    Implements automatic fallback chain for resilience.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 500,
        fallback_chain: Optional[List[str]] = None
    ):
        """
        Initialize OpenAI LLM client.
        
        Args:
            api_key: OpenAI API key. If not provided, reads from OPENAI_API_KEY env var.
            model: The model to use (e.g., 'gpt-3.5-turbo', 'gpt-4', 'gpt-5-nano').
            temperature: Sampling temperature (0.0 to 2.0). Not used for GPT-5 models.
            max_tokens: Maximum tokens in the response.
            fallback_chain: Optional custom fallback chain. If None, uses default based on model.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        self.model = model
        self.temperature = temperature
        
        # For gpt-5 models, use lower default max_tokens to maintain coherence
        # GPT-5 Nano requires explicit max_output_tokens and works better with shorter responses
        if model.startswith("gpt-5"):
            # GPT-5 Nano works better with shorter responses (~200-600 tokens)
            # But ensure minimum of 50 tokens to avoid empty responses
            if max_tokens == 500:  # Default value, override it
                self.max_tokens = 200
            else:
                # Ensure minimum of 50 tokens, maximum of 600 for GPT-5 models
                self.max_tokens = max(50, min(max_tokens, 600))
        else:
            self.max_tokens = max_tokens
        
        # Configure fallback chain
        self.fallback_enabled = settings.llm_fallback_enabled
        self.fallback_chain = fallback_chain or self._get_fallback_chain(model)
        self.streaming_timeout = settings.llm_streaming_timeout
        
        # Cache for failed models (with cooldown)
        self.failed_models: dict[str, float] = {}  # model -> timestamp of last failure
        self.failure_cooldown = 300  # 5 minutes in seconds
        
        self._client = None
    
    def _get_fallback_chain(self, primary_model: str) -> List[str]:
        """
        Define the fallback chain based on the primary model.
        
        Args:
            primary_model: The primary model to use.
            
        Returns:
            List of models to try in order.
        """
        chains = {
            "gpt-5-nano": ["gpt-5-nano", "gpt-5-mini", "gpt-4", "gpt-3.5-turbo"],
            "gpt-5-mini": ["gpt-5-mini", "gpt-4", "gpt-3.5-turbo"],
            "gpt-5": ["gpt-5", "gpt-4", "gpt-3.5-turbo"],
            "gpt-4": ["gpt-4", "gpt-3.5-turbo"],
            "gpt-3.5-turbo": ["gpt-3.5-turbo"],
        }
        
        # Try exact match first
        if primary_model in chains:
            return chains[primary_model]
        
        # Try prefix match for gpt-5 variants
        if primary_model.startswith("gpt-5"):
            if "nano" in primary_model:
                return chains["gpt-5-nano"]
            elif "mini" in primary_model:
                return chains["gpt-5-mini"]
            else:
                return chains["gpt-5"]
        
        # Default: just use the primary model
        return [primary_model]
    
    def _should_skip_model(self, model: str) -> bool:
        """
        Check if a model should be skipped due to recent failure.
        
        Args:
            model: The model to check.
            
        Returns:
            True if model should be skipped, False otherwise.
        """
        if not self.fallback_enabled:
            return False
        
        if model in self.failed_models:
            last_failure = self.failed_models[model]
            if time.time() - last_failure < self.failure_cooldown:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Skipping model {model} (failed recently, cooldown active)")
                return True
        
        return False
    
    def _mark_model_failed(self, model: str):
        """Mark a model as failed (for cooldown)."""
        self.failed_models[model] = time.time()
    
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
    
    def _get_completion_params(self):
        """
        Get the correct parameters for API call based on model.
        
        Legacy models (gpt-3.5, gpt-4) use max_tokens and temperature.
        Newer models (gpt-5-*) use max_output_tokens and don't support temperature.
        """
        params = {}
        
        if self.model.startswith("gpt-5"):
            # GPT-5 models use max_output_tokens (not max_tokens!)
            params["max_output_tokens"] = self.max_tokens
            # GPT-5 models only support default temperature, don't send it
        elif self.model.startswith("o1"):
            # o1 models use max_tokens and don't support temperature
            params["max_tokens"] = self.max_tokens
        else:
            # Legacy models (gpt-3.5, gpt-4)
            params["max_tokens"] = self.max_tokens
            params["temperature"] = self.temperature
        
        return params
    
    def _extract_text_from_response(self, response, logger=None) -> str:
        """
        Extract text from OpenAI response object, handling different response formats.
        
        Args:
            response: The response object from OpenAI API.
            logger: Optional logger for debugging.
            
        Returns:
            The extracted text as a string, or empty string if not found.
        """
        if logger:
            logger.debug(f"Extracting text from response: type={type(response)}")
            if hasattr(response, '__dict__'):
                logger.debug(f"Response attributes: {list(response.__dict__.keys())}")
            elif isinstance(response, dict):
                logger.debug(f"Response dict keys: {list(response.keys())}")
        
        output_text = None
        
        # Try different ways to get the output text
        if hasattr(response, 'output_text'):
            output_text = response.output_text
            if logger:
                logger.debug(f"Found output_text attribute: {type(output_text)}, value={repr(output_text)[:100]}")
        elif hasattr(response, 'output'):
            output_text = response.output
            if logger:
                logger.debug(f"Found output attribute: {type(output_text)}, value={repr(output_text)[:100]}")
        elif hasattr(response, 'text'):
            output_text = response.text
            if logger:
                logger.debug(f"Found text attribute: {type(output_text)}, value={repr(output_text)[:100]}")
        elif isinstance(response, dict):
            output_text = response.get('output_text') or response.get('output') or response.get('text')
            if logger:
                logger.debug(f"Found in dict: {type(output_text)}, value={repr(output_text)[:100] if output_text else None}")
        
        # Try additional attributes that might contain the text
        if output_text is None or (isinstance(output_text, str) and not output_text.strip()):
            # Try other common attributes
            for attr_name in ['content', 'message', 'response', 'result', 'data']:
                if hasattr(response, attr_name):
                    attr_value = getattr(response, attr_name)
                    if logger:
                        logger.debug(f"Trying attribute {attr_name}: {type(attr_value)}")
                    if attr_value:
                        # If it's a dict/object, try to get text from it
                        if isinstance(attr_value, dict):
                            output_text = attr_value.get('text') or attr_value.get('content') or attr_value.get('output_text')
                        elif isinstance(attr_value, str):
                            output_text = attr_value
                        elif hasattr(attr_value, 'text'):
                            output_text = attr_value.text
                        elif hasattr(attr_value, 'content'):
                            output_text = attr_value.content
                        
                        if output_text:
                            break
        
        # Normalize to string: if it's a list, join it; if it's None, use empty string
        if output_text is None:
            if logger:
                logger.warning("Could not extract text from response - all extraction methods failed")
            return ""
        elif isinstance(output_text, list):
            # If it's a list, join the elements (assuming they're strings or can be converted)
            result = " ".join(str(item) for item in output_text if item)
            if logger:
                logger.debug(f"Joined list to string: {len(result)} chars")
            return result
        elif isinstance(output_text, str):
            if logger:
                logger.debug(f"Extracted string: {len(output_text)} chars")
            return output_text
        else:
            # Convert to string as fallback
            result = str(output_text)
            if logger:
                logger.debug(f"Converted to string: {len(result)} chars")
            return result
    
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
            # GPT-5 models use responses API, not chat.completions
            if self.model.startswith("gpt-5"):
                import logging
                logger = logging.getLogger(__name__)
                
                max_tokens_for_model = self._get_max_tokens_for_model(self.model)
                logger.debug(f"Using max_output_tokens={max_tokens_for_model} for {self.model}")
                
                response = await client.responses.create(
                    model=self.model,
                    input=message,
                    max_output_tokens=max_tokens_for_model
                )
                
                # Debug: Log response structure
                logger.info(f"Response from {self.model}: type={type(response)}, dir={dir(response)}")
                if hasattr(response, '__dict__'):
                    logger.info(f"Response attributes: {response.__dict__}")
                
                # Extract and normalize text from response
                output_text = self._extract_text_from_response(response, logger)
                logger.info(f"Extracted output_text: {repr(output_text)}")
                return output_text
            
            # Legacy models (gpt-3.5, gpt-4) use chat.completions
            completion_params = self._get_completion_params()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": message}
                ],
                **completion_params
            )
            
            return response.choices[0].message.content or ""
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}") from e
    
    async def _try_stream_with_model(self, model: str, message: str, client) -> AsyncGenerator[str, None]:
        """
        Try to stream with a specific model.
        
        Args:
            model: The model to try.
            message: The input message.
            client: The OpenAI client.
            
        Yields:
            Chunks if successful.
            
        Raises:
            RuntimeError: If streaming fails or returns no chunks.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if model.startswith("gpt-5"):
            # GPT-5 models use responses API
            chunks_yielded = 0
            async with client.responses.stream(
                model=model,
                input=message,
                max_output_tokens=self.max_tokens
            ) as stream:
                async for event in stream:
                    if event.type == "response.output_text.delta":
                        if event.delta:
                            chunks_yielded += 1
                            yield event.delta
            
            if chunks_yielded == 0:
                raise RuntimeError(f"{model} returned stream with no chunks")
            
            logger.info(f"Streaming successful with {model}: {chunks_yielded} chunks")
        else:
            # Legacy models use chat.completions
            completion_params = self._get_completion_params_for_model(model)
            stream = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": message}
                ],
                stream=True,
                **completion_params
            )
            
            chunks_yielded = 0
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    choice = chunk.choices[0]
                    if hasattr(choice, 'delta') and choice.delta:
                        delta = choice.delta
                        content = getattr(delta, 'content', None)
                        if content:
                            chunks_yielded += 1
                            yield content
            
            if chunks_yielded == 0:
                raise RuntimeError(f"{model} returned stream with no chunks")
            
            logger.info(f"Streaming successful with legacy model {model}: {chunks_yielded} chunks")
    
    def _get_max_tokens_for_model(self, model: str) -> int:
        """
        Get appropriate max_tokens value for a specific model.
        
        Different models have different optimal token limits.
        """
        if model.startswith("gpt-5"):
            # GPT-5 models work better with 200-600 tokens
            # Use the configured value, but ensure it's within reasonable bounds
            return max(50, min(self.max_tokens, 600))
        else:
            # Legacy models can handle more tokens
            return self.max_tokens
    
    def _get_completion_params_for_model(self, model: str) -> dict:
        """Get completion params for a specific model (not necessarily self.model)."""
        params = {}
        max_tokens_for_model = self._get_max_tokens_for_model(model)
        
        if model.startswith("gpt-5"):
            params["max_output_tokens"] = max_tokens_for_model
        elif model.startswith("o1"):
            params["max_tokens"] = max_tokens_for_model
        else:
            params["max_tokens"] = max_tokens_for_model
            params["temperature"] = self.temperature
        
        return params
    
    async def _generate_and_simulate_stream(
        self,
        model: str,
        message: str,
        client,
        chunk_size: int = 20,
        sleep_time: float = 0.005
    ) -> AsyncGenerator[str, None]:
        """
        Generate full response and simulate streaming quickly.
        
        Used as fallback when native streaming fails.
        Optimized for speed with larger chunks and minimal sleep.
        
        Args:
            model: The model to use.
            message: The input message.
            client: The OpenAI client.
            chunk_size: Size of chunks for simulated streaming (default: 20).
            sleep_time: Sleep time between chunks in seconds (default: 0.005).
        """
        import logging
        import asyncio
        logger = logging.getLogger(__name__)
        
        if model.startswith("gpt-5"):
            if logger:
                logger.debug(f"Calling responses.create for {model} with input length: {len(message)}")
            
            try:
                max_tokens_for_model = self._get_max_tokens_for_model(model)
                if logger:
                    logger.debug(f"Using max_output_tokens={max_tokens_for_model} for {model}")
                
                response = await client.responses.create(
                    model=model,
                    input=message,
                    max_output_tokens=max_tokens_for_model
                )
                
                if logger:
                    logger.debug(f"Response received: type={type(response)}")
                    if hasattr(response, '__dict__'):
                        logger.debug(f"Response keys: {list(response.__dict__.keys())}")
                
                # Extract and normalize text from response
                full_response = self._extract_text_from_response(response, logger)
                
                if logger:
                    logger.debug(f"Extracted response length: {len(full_response)} chars")
            except Exception as e:
                if logger:
                    logger.error(f"Error calling responses.create for {model}: {e}")
                raise
        else:
            # Legacy models
            completion_params = self._get_completion_params_for_model(model)
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": message}
                ],
                **completion_params
            )
            full_response = response.choices[0].message.content or ""
        
        if not full_response:
            # Log detailed information about the empty response
            if logger:
                logger.warning(
                    f"{model} returned empty response. "
                    f"Response type: {type(response)}, "
                    f"Response attributes: {dir(response) if hasattr(response, '__dict__') else 'N/A'}"
                )
            raise RuntimeError(f"{model} returned empty response")
        
        # Simulate streaming with optimized chunk size and sleep time
        for i in range(0, len(full_response), chunk_size):
            yield full_response[i:i + chunk_size]
            await asyncio.sleep(sleep_time)
        
        logger.info(f"Simulated streaming completed with {model}: {len(full_response)} characters")
    
    async def generate_stream(self, message: str) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response using OpenAI API with optimized fallback.
        
        Optimizations:
        - Skip models that failed recently (cooldown)
        - Use minimal fallback chain (primary + one fallback)
        - Simulate streaming with larger chunks and minimal sleep
        - Log and cache failures efficiently
        
        Args:
            message: The input message/prompt.
            
        Yields:
            Chunks of the generated response as they become available.
            
        Raises:
            Exception: If all models in the optimized fallback chain fail.
        """
        client = self._get_client()
        import logging
        import asyncio
        logger = logging.getLogger(__name__)
        
        if not self.fallback_enabled:
            # Fallback disabled, just try primary model
            async for chunk in self._try_stream_with_model(self.model, message, client):
                yield chunk
            return
        
        # Build optimized fallback chain
        # For GPT-5 models, ensure we have reliable fallbacks (gpt-4, gpt-3.5-turbo)
        optimized_chain = [self.model]
        
        # Add configured fallback chain models
        for fallback_model in self.fallback_chain:
            if fallback_model != self.model and fallback_model not in optimized_chain:
                optimized_chain.append(fallback_model)
        
        # Ensure we have at least gpt-4 and gpt-3.5-turbo as final fallbacks for GPT-5 models
        if "gpt-5" in self.model:
            if "gpt-4" not in optimized_chain:
                optimized_chain.append("gpt-4")
            if "gpt-3.5-turbo" not in optimized_chain:
                optimized_chain.append("gpt-3.5-turbo")
        
        logger.info(f"Fallback chain: {optimized_chain}")
        last_error = None
        
        for model in optimized_chain:
            # Skip models that failed recently
            if self._should_skip_model(model):
                continue
            
            try:
                logger.info(f"Attempting streaming with model: {model}")
                
                # Try native streaming first
                try:
                    async for chunk in self._try_stream_with_model(model, message, client):
                        yield chunk
                    # Success, clear failure cache
                    self.failed_models.pop(model, None)
                    return
                except Exception as stream_error:
                    logger.warning(
                        f"Native streaming failed with {model}: {stream_error}. "
                        "Falling back to fast simulated streaming..."
                    )
                    
                    # Fast simulated streaming fallback
                    try:
                        # Use larger chunks and minimal sleep for speed
                        async for chunk in self._generate_and_simulate_stream(
                            model, message, client, chunk_size=20, sleep_time=0.005
                        ):
                            yield chunk
                        # Success, clear failure cache
                        self.failed_models.pop(model, None)
                        return
                    except Exception as non_stream_error:
                        logger.warning(
                            f"Fallback simulated streaming failed for {model}: {non_stream_error}"
                        )
                        self._mark_model_failed(model)
                        last_error = non_stream_error
                        continue  # Try next model
                        
            except Exception as e:
                last_error = e
                logger.warning(f"Model {model} completely failed: {str(e)[:100]}...")
                self._mark_model_failed(model)
                continue
        
        # All models failed
        logger.error(f"All models in optimized fallback failed. Last error: {last_error}")
        raise RuntimeError(
            f"All models failed: {', '.join(optimized_chain)}. Last error: {last_error}"
        ) from last_error
