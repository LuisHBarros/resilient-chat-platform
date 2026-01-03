# Streaming Message Processing Flow

## Sequence Diagram - Streaming with SSE

```
Frontend          API Layer        Use Case        LLM Provider    Repository
   │                  │                │                │              │
   │  POST /stream    │                │                │              │
   ├─────────────────>│                │                │              │
   │                  │                │                │              │
   │                  │ Validate DTO   │                │              │
   │                  │                │                │              │
   │                  │ get_use_case() │                │              │
   │                  ├───────────────>│                │              │
   │                  │                │                │              │
   │                  │ StreamingResponse               │              │
   │<─────────────────┤                │                │              │
   │                  │                │                │              │
   │                  │ execute()      │                │              │
   │                  ├───────────────>│                │              │
   │                  │                │                │              │
   │                  │                │ Load/Create    │              │
   │                  │                │ Conversation  │              │
   │                  │                ├──────────────────────────────>│
   │                  │                │                │              │
   │                  │                │<──────────────────────────────┤
   │                  │                │                │              │
   │                  │                │ Save user msg  │              │
   │                  │                ├──────────────────────────────>│
   │                  │                │                │              │
   │                  │                │<──────────────────────────────┤
   │                  │                │                │              │
   │                  │                │ generate_stream()              │
   │                  │                ├──────────────────────────────>│
   │                  │                │                │              │
   │                  │                │                │ Try Model 1  │
   │                  │                │                │ (gpt-5-nano)  │
   │                  │                │                ├──────────────>│
   │                  │                │                │              │
   │                  │                │                │<──────────────┤
   │                  │                │                │ (empty)       │
   │                  │                │                │              │
   │                  │                │                │ Try Model 2  │
   │                  │                │                │ (gpt-5-mini)  │
   │                  │                │                ├──────────────>│
   │                  │                │                │              │
   │                  │                │                │<──────────────┤
   │                  │                │                │ (chunks)      │
   │                  │                │                │              │
   │  data: {chunk}   │                │                │              │
   │<─────────────────┤                │                │              │
   │                  │                │                │              │
   │  data: {chunk}   │                │                │              │
   │<─────────────────┤                │                │              │
   │                  │                │                │              │
   │  data: {chunk}   │                │                │              │
   │<─────────────────┤                │                │              │
   │                  │                │                │              │
   │                  │                │                │              │
   │                  │                │ Save assistant │              │
   │                  │                │ message        │              │
   │                  │                ├──────────────────────────────>│
   │                  │                │                │              │
   │                  │                │<──────────────────────────────┤
   │                  │                │                │              │
   │  [done]          │                │                │              │
   │<─────────────────┤                │                │              │
```

## Detailed Flow

### 1. Request Reception
- Frontend sends POST request to `/api/v1/chat/message/stream`
- Request includes: `message`, `user_id` (optional), `conversation_id` (optional)
- CORS middleware allows cross-origin request

### 2. API Layer Processing
- **Middleware**: 
  - Correlation ID middleware adds `X-Correlation-ID` header
  - CORS middleware handles preflight and adds CORS headers
- **Validation**: `MessageRequestDTO` validates input
- **Streaming Response**: FastAPI creates `StreamingResponse` with `text/event-stream` media type
- **Dependency Injection**: FastAPI injects `StreamMessageUseCase`

### 3. Use Case Execution
- **Load/Create Conversation**: 
  - If `conversation_id` provided, load from repository
  - If not found, create new conversation (graceful handling)
  - If not provided, create new conversation
- **Save User Message**: Create and save user message immediately
- **Stream LLM Response**: 
  - Call `llm.generate_stream()` which yields chunks
  - Accumulate chunks using `StringIO` for efficiency
  - Enforce `MAX_RESPONSE_CHARS` limit (4000 chars)
  - Yield each chunk as SSE event: `data: {"chunk": "...", "type": "content"}\n\n`

### 4. LLM Provider - Fallback Mechanism
- **Primary Model**: Try `gpt-5-nano` with native streaming
- **Fallback Stage 1**: If streaming fails or returns empty, try simulated streaming
- **Fallback Stage 2**: If still fails, try next model in chain (`gpt-5-mini`)
- **Fallback Stage 3**: Continue through chain (`gpt-4`, `gpt-3.5-turbo`)
- **Failure Cooldown**: Models that fail are temporarily skipped (5-minute cooldown)

### 5. Streaming Format
- **SSE Event Format**: `data: {json}\n\n`
- **Content Chunk**: `{"chunk": "text", "type": "content"}`
- **Error Event**: `{"error": "message", "type": "error"}`
- **Headers**: `Cache-Control: no-cache`, `Connection: keep-alive`

### 6. Response Accumulation
- Chunks accumulated in `StringIO` buffer
- Response length tracked to enforce limits
- Full response saved as assistant message after streaming completes

### 7. Error Handling
- **LLM Errors**: Sent as SSE error events, error state saved to conversation
- **Streaming Errors**: Logged with correlation ID, error event sent to client
- **Repository Errors**: Logged, error event sent to client
- **Connection Drops**: Partial response saved if possible

## Fallback Chain Example

```
gpt-5-nano (Primary)
    │
    ├─ Native Streaming ──┐
    │                     │
    │                     ├─ Success → Return chunks
    │                     │
    │                     └─ Failure → Simulated Streaming
    │                                   │
    │                                   ├─ Success → Return chunks
    │                                   │
    │                                   └─ Failure → Next Model
    │
gpt-5-mini (Fallback 1)
    │
    ├─ [Same process]
    │
gpt-4 (Fallback 2)
    │
    ├─ [Same process]
    │
gpt-3.5-turbo (Fallback 3)
    │
    ├─ [Same process]
    │
All Failed → Error Event
```

## Error Scenarios

### 1. Empty Streaming Response
- **Detection**: No chunks received after stream completes
- **Action**: Fallback to simulated streaming, then next model
- **Logging**: Warning logged with correlation ID

### 2. API Error
- **Detection**: Exception from LLM API
- **Action**: Catch exception, try next model in chain
- **Logging**: Error logged with exception details

### 3. Network Timeout
- **Detection**: Timeout exception
- **Action**: Try next model in chain
- **Logging**: Warning logged

### 4. Empty Response
- **Detection**: Response extraction returns empty string
- **Action**: Try next model in chain
- **Logging**: Warning logged with response structure

## Frontend Integration

### EventSource API
```javascript
const eventSource = new EventSource('/api/v1/chat/message/stream');
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'content') {
    appendChunk(data.chunk);
  } else if (data.type === 'error') {
    handleError(data.error);
  }
};
```

### Fetch API (Alternative)
```javascript
const response = await fetch('/api/v1/chat/message/stream', {
  method: 'POST',
  body: JSON.stringify({ message: 'Hello' })
});
const reader = response.body.getReader();
// Process chunks...
```

## Performance Considerations

- **StringIO**: Efficient string accumulation (O(n) vs O(n²) for list concatenation)
- **Response Limits**: `MAX_RESPONSE_CHARS = 4000` prevents excessive costs
- **Chunk Size**: Simulated streaming uses 20-char chunks with 5ms sleep
- **Cooldown**: Failed models skipped for 5 minutes to avoid repeated failures
- **Connection Keep-Alive**: SSE maintains connection for multiple chunks

## Logging Points

1. **Request received**: Log with correlation ID, user_id, message length
2. **Conversation loaded/created**: Log conversation_id
3. **User message saved**: Log before streaming starts
4. **LLM model attempt**: Log model name, attempt number
5. **Fallback triggered**: Log reason, next model
6. **Chunks received**: Log chunk count, total length
7. **Streaming completed**: Log total response length
8. **Assistant message saved**: Log after streaming completes
9. **Error occurred**: Log error type, message, context, correlation ID

