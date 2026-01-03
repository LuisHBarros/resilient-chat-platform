# ADR-0007: OpenAI API Responses vs Chat Completions (GPT-5 Models)

## Status
Accepted

## Context
OpenAI introduced new models (GPT-5 series) that use a different API endpoint:
- **Legacy models** (GPT-3.5, GPT-4): Use `chat.completions` API
- **New models** (GPT-5-nano, GPT-5-mini): Use `responses` API

Key differences:
- Different API endpoints (`/v1/chat/completions` vs `/v1/responses`)
- Different parameters (`max_tokens` vs `max_output_tokens`)
- Different response structure
- Different streaming format
- GPT-5 models don't support custom temperature (only default)

We need to support both APIs while maintaining a clean abstraction.

## Decision
We implemented API-specific handling in `OpenAIProvider` based on model name:

1. **Model Detection**: Check if model starts with `gpt-5`
2. **API Selection**: 
   - GPT-5 models → `client.responses.create()` / `client.responses.stream()`
   - Legacy models → `client.chat.completions.create()` / `client.chat.completions.create(stream=True)`
3. **Parameter Mapping**: 
   - GPT-5: `max_output_tokens` (no `temperature`)
   - Legacy: `max_tokens` + `temperature`
4. **Response Extraction**: Different methods for each API type
5. **Unified Interface**: `LLMPort` hides these differences

### Implementation:
```python
if model.startswith("gpt-5"):
    # Use responses API
    response = await client.responses.create(
        model=model,
        input=message,  # Simple string, not messages array
        max_output_tokens=max_tokens
    )
    output_text = self._extract_text_from_response(response)
else:
    # Use chat.completions API
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": message}],
        max_tokens=max_tokens,
        temperature=temperature
    )
    output_text = response.choices[0].message.content
```

### Key Differences:

| Aspect | Chat Completions | Responses API |
|--------|-----------------|---------------|
| Endpoint | `/v1/chat/completions` | `/v1/responses` |
| Input | `messages` array | `input` string |
| Max Tokens | `max_tokens` | `max_output_tokens` |
| Temperature | Supported | Default only |
| Streaming | `stream=True` | `responses.stream()` |
| Response | `choices[0].message.content` | `output_text` attribute |

## Consequences

### Positive:
- ✅ Supports both legacy and new models
- ✅ Clean abstraction (use case doesn't know which API)
- ✅ Future-proof (easy to add new model types)
- ✅ Handles API differences transparently
- ✅ Maintains backward compatibility

### Negative:
- ⚠️ More complex provider implementation
- ⚠️ Need to maintain two code paths
- ⚠️ Different error handling for each API
- ⚠️ Response extraction more complex (needs normalization)
- ⚠️ Testing requires knowledge of both APIs

## Implementation Details

- `_get_completion_params()`: Returns appropriate params per model
- `_get_completion_params_for_model()`: Gets params for specific model in fallback chain
- `_extract_text_from_response()`: Normalizes response extraction (handles lists, strings, etc.)
- `_try_stream_with_model()`: Handles streaming for both APIs
- `_generate_and_simulate_stream()`: Handles non-streaming for both APIs

## Error Handling

Common errors handled:
- `max_tokens` not supported → Use `max_output_tokens` for GPT-5
- `temperature` not supported → Remove for GPT-5
- Empty responses → Normalize extraction
- List responses → Join to string

## Alternatives Considered

1. **Separate Providers**: `OpenAIProvider` and `OpenAIResponsesProvider` - Too much duplication
2. **Wrapper Classes**: Add abstraction layer - Adds complexity without benefit
3. **Configuration-Based**: Map models to APIs - Less flexible
4. **Single API Only**: Support only one API - Limits model options

## Future Enhancements

- Add support for more GPT-5 variants
- Add automatic API detection (if possible)
- Add API versioning support
- Add response format validation

## References
- [OpenAI Chat Completions API](https://platform.openai.com/docs/api-reference/chat)
- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses) (when available)

