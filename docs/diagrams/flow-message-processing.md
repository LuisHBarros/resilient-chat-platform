# Message Processing Flow

## Sequence Diagram

```
User          API Layer        Use Case        Domain        Infrastructure
 │                │                │              │                │
 │  POST /message │                │              │                │
 ├───────────────>│                │              │                │
 │                │                │              │                │
 │                │ Validate DTO   │              │                │
 │                │                │              │                │
 │                │ get_use_case()│              │                │
 │                ├───────────────>│              │                │
 │                │                │              │                │
 │                │                │ execute()    │                │
 │                ├───────────────>│              │                │
 │                │                │              │                │
 │                │                │ Create       │                │
 │                │                │ Message VO   │                │
 │                │                ├─────────────>│                │
 │                │                │              │                │
 │                │                │ Load/Create  │                │
 │                │                │ Conversation │                │
 │                │                ├─────────────>│                │
 │                │                │              │                │
 │                │                │ find_by_id()│                │
 │                │                ├──────────────────────────────>│
 │                │                │              │                │
 │                │                │              │                │
 │                │                │<──────────────────────────────┤
 │                │                │              │                │
 │                │                │              │                │
 │                │                │ generate()   │                │
 │                │                ├──────────────────────────────>│
 │                │                │              │   (LLM API)   │
 │                │                │              │                │
 │                │                │              │                │
 │                │                │<──────────────────────────────┤
 │                │                │              │                │
 │                │                │              │                │
 │                │                │ save()       │                │
 │                │                ├──────────────────────────────>│
 │                │                │              │                │
 │                │                │              │                │
 │                │                │<──────────────────────────────┤
 │                │                │              │                │
 │                │                │              │                │
 │                │<───────────────┤              │                │
 │                │                │              │                │
 │<───────────────┤                │              │                │
 │                │                │              │                │
```

## Detailed Flow

### 1. Request Reception
- User sends POST request to `/api/v1/chat/message`
- Request includes: `message`, `user_id` (optional), `conversation_id` (optional)

### 2. API Layer Processing
- **Middleware**: Correlation ID middleware adds `X-Correlation-ID` header
- **Validation**: `MessageRequestDTO` validates input (message not empty, length limits)
- **Dependency Injection**: FastAPI calls `get_process_message_use_case(request)`
- **Composition Root**: `bootstrap.py` creates use case with all dependencies

### 3. Use Case Execution
- **Load Conversation**: If `conversation_id` provided, load from repository
- **Create Message**: Create `Message` value object with user content
- **Add to Conversation**: Add message to conversation entity
- **Generate Response**: Call LLM port to generate response
- **Create Assistant Message**: Create `Message` value object with response
- **Save Conversation**: Persist conversation with both messages

### 4. Domain Layer
- **Entities**: `Conversation` enforces business rules (user_id required, etc.)
- **Value Objects**: `Message` validates content and role
- **Ports**: Define contracts for LLM and Repository

### 5. Infrastructure Layer
- **LLM Adapter**: Calls external LLM API (OpenAI, Bedrock, or Mock)
- **Repository**: Saves/loads conversations (currently in-memory)
- **Logging**: Structured logs with correlation ID

### 6. Response
- Use case returns result dictionary
- API layer converts to `MessageResponseDTO`
- Response includes: `conversation_id`, `response`, `user_message`, `assistant_message`

## Error Handling

### Domain Exceptions
- `InvalidMessageError`: Message violates domain rules
- `LLMError`: LLM operation failed
- `RepositoryError`: Repository operation failed

### Application Exceptions
- `UseCaseError`: Use case execution failed
- `ValidationError`: Input validation failed

### Infrastructure Exceptions
- `LLMProviderError`: LLM provider specific error
- `DatabaseError`: Database operation failed
- `ConfigurationError`: Configuration invalid

### HTTP Status Codes
- `200 OK`: Success (or StreamingResponse for SSE)
- `400 Bad Request`: Application error (validation, etc.)
- `500 Internal Server Error`: Repository error
- `503 Service Unavailable`: LLM or infrastructure error

### Streaming Error Handling
- Errors sent as SSE events: `data: {"error": "...", "type": "error"}\n\n`
- Error state saved to conversation for debugging
- Streaming continues (sends error event) instead of crashing
- Fallback mechanism automatically tries alternative models

## Logging Points

1. **Request received**: Log with correlation ID, user_id, message length
2. **Conversation loaded**: Log conversation_id, message count
3. **LLM call**: Log before and after LLM generation
4. **Error occurred**: Log error type, message, context
5. **Request completed**: Log success, conversation_id, total messages

