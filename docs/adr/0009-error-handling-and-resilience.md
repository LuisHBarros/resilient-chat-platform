# ADR-0009: Error Handling and Resilience

## Status
Accepted

## Context
Our system needs to handle various failure scenarios gracefully:
- LLM API failures (rate limits, timeouts, errors)
- Empty responses from models
- Network issues
- Invalid input
- Database errors
- Streaming failures

We need:
- User-friendly error messages
- System resilience (automatic recovery)
- Proper error logging
- Error state persistence
- Graceful degradation

## Decision
We implemented a multi-layered error handling strategy:

### 1. **Domain Exceptions**
Custom exceptions in `domain/exceptions.py`:
- `LLMError`: LLM-related errors
- `RepositoryError`: Persistence errors
- `ApplicationException`: Application logic errors
- `InfrastructureException`: Infrastructure errors

### 2. **Error Propagation**
- Use cases raise domain exceptions
- API layer catches and converts to HTTP responses
- Errors logged with correlation ID for tracing

### 3. **Streaming Error Handling**
- Errors sent as SSE events: `data: {"error": "...", "type": "error"}`
- Error state saved to conversation
- Streaming continues (sends error event) instead of crashing

### 4. **Fallback Mechanisms**
- LLM fallback chain (see ADR-0006)
- Simulated streaming when native streaming fails
- Empty response handling with retry

### 5. **Response Limits**
- `MAX_RESPONSE_CHARS = 4000` to prevent excessive costs
- Response truncation with warning logs
- Memory-efficient accumulation (StringIO)

### Implementation:
```python
# Use case error handling
try:
    async for chunk in self.llm.generate_stream(message):
        yield chunk
except LLMError as e:
    # Log error
    # Save error state
    # Yield error event
    yield error_event

# API error handling
try:
    return StreamingResponse(stream_generator())
except (LLMError, RepositoryError) as e:
    raise HTTPException(status_code=500, detail=str(e))
```

## Consequences

### Positive:
- ✅ Graceful error handling (no crashes)
- ✅ User-friendly error messages
- ✅ Error state persistence (can debug later)
- ✅ Automatic recovery (fallbacks)
- ✅ Proper logging (correlation IDs)
- ✅ Cost protection (response limits)

### Negative:
- ⚠️ More complex error handling code
- ⚠️ Need to handle errors at multiple layers
- ⚠️ Error messages may leak implementation details (mitigated)
- ⚠️ Error state adds complexity

## Error Types and Handling

### LLM Errors
- **Rate Limits**: Fallback to next model
- **Timeouts**: Retry with fallback
- **Empty Responses**: Try fallback, then simulate streaming
- **API Errors**: Catch, log, try fallback

### Repository Errors
- **Not Found**: Create new resource (for conversations)
- **Save Errors**: Log, return error to user
- **Connection Errors**: Log, return error to user

### Streaming Errors
- **Connection Drops**: Log, save partial response
- **Chunk Errors**: Log, continue with next chunk
- **Empty Streams**: Fallback to simulated streaming

## Error Response Format

### SSE Error Event:
```json
{
  "error": "Failed to generate streaming LLM response: ...",
  "type": "error"
}
```

### HTTP Error Response:
```json
{
  "detail": "Failed to generate LLM response: ..."
}
```

## Logging Strategy

- **Error Level**: Actual errors (exceptions, failures)
- **Warning Level**: Recoverable issues (fallbacks, empty responses)
- **Info Level**: Normal operations (processing, saving)
- **Debug Level**: Detailed information (response structure, extraction)

All logs include:
- Correlation ID
- User ID
- Conversation ID
- Error details
- Context (model, message length, etc.)

## Alternatives Considered

1. **Fail Fast**: Simple but poor UX
2. **Silent Failures**: Bad for debugging
3. **Generic Errors**: Less helpful for users
4. **No Error Persistence**: Harder to debug
5. **No Fallbacks**: Poor resilience

## Future Enhancements

- Add error retry with exponential backoff
- Add error rate limiting
- Add error alerting (PagerDuty, etc.)
- Add error analytics dashboard
- Add user-facing error codes
- Add error recovery suggestions

## References
- [Error Handling Best Practices](https://docs.microsoft.com/en-us/dotnet/standard/exceptions/best-practices-for-exceptions)
- [Resilience Patterns](https://docs.microsoft.com/en-us/azure/architecture/patterns/category/resilience)

