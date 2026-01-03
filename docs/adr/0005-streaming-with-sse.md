# ADR-0005: Streaming with Server-Sent Events (SSE)

## Status
Accepted

## Context
We need to provide real-time streaming responses to users because:
- Users expect ChatGPT-like experience with streaming text
- Reduces perceived latency (users see response as it's generated)
- Better UX for long responses
- Industry standard for chat applications

Traditional request-response pattern requires waiting for complete response, which:
- Feels slow to users
- Doesn't provide real-time feedback
- Can timeout on long responses

## Decision
We implemented streaming using Server-Sent Events (SSE) with FastAPI's `StreamingResponse`:

1. **Streaming Endpoint**: `/api/v1/chat/message/stream` returns `StreamingResponse`
2. **SSE Format**: Chunks sent as `data: {json}\n\n` format
3. **Use Case Pattern**: `StreamMessageUseCase` yields chunks as they're generated
4. **Data Persistence**: User message saved immediately, assistant message saved after streaming completes
5. **Error Handling**: Errors sent as SSE events, maintaining connection

### Architecture:
```
Frontend                    Backend
   |                           |
   |-- POST /stream ---------->|
   |                           |-- Save user message
   |<-- data: {chunk} ---------|
   |<-- data: {chunk} ---------|
   |<-- data: {chunk} ---------|
   |                           |-- Save assistant message
   |<-- [done] ----------------|
```

### Implementation Details:
- `StreamMessageUseCase` in `application/use_cases/stream_message.py`
- Uses `StringIO` for efficient response accumulation
- Response length limit (`MAX_RESPONSE_CHARS = 4000`) to prevent excessive costs
- SSE format: `data: {"chunk": "text", "type": "content"}\n\n`
- Error format: `data: {"error": "message", "type": "error"}\n\n`

## Consequences

### Positive:
- ✅ Real-time user experience (ChatGPT-like)
- ✅ Reduced perceived latency
- ✅ Works with standard HTTP (no WebSocket complexity)
- ✅ Easy to implement on frontend (EventSource API)
- ✅ Maintains data persistence (messages saved)
- ✅ Graceful error handling (errors sent as events)

### Negative:
- ⚠️ More complex than request-response
- ⚠️ Need to handle connection drops gracefully
- ⚠️ Response accumulation uses memory (mitigated with StringIO and limits)
- ⚠️ SSE has limitations (one-way, text only, but sufficient for our use case)

## Alternatives Considered

1. **WebSockets**: More complex, bidirectional (we don't need), harder to scale
2. **Polling**: Simple but inefficient, high latency
3. **Long Polling**: Better than polling but still not real-time
4. **HTTP/2 Server Push**: Not widely supported, complex
5. **Request-Response**: Simple but poor UX for chat

## Implementation Notes

- Frontend uses `EventSource` or `fetch` with streaming
- Backend uses FastAPI's `StreamingResponse` with `text/event-stream` media type
- Headers set: `Cache-Control: no-cache`, `Connection: keep-alive`
- Response chunks accumulated using `StringIO` for efficiency
- Maximum response length enforced to prevent excessive costs

## Future Enhancements

- Add cancellation support (client disconnect)
- Add progress indicators
- Add retry mechanism for failed chunks
- Add compression for large responses

## References
- [Server-Sent Events (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [FastAPI StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [SSE Specification](https://html.spec.whatwg.org/multipage/server-sent-events.html)

