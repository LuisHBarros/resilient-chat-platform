# API Documentation

Complete REST API documentation for the Chat Service.

## 📋 Table of Contents

- [Overview](#overview)
- [Base URL](#base-url)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
- [Data Models](#data-models)
- [Status Codes](#status-codes)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Observability](#observability)

## Overview

The Chat Service API provides endpoints for:
- Sending messages and receiving AI responses
- Real-time response streaming (SSE)
- Health checks and readiness probes
- Conversation management

The API follows REST principles and uses:
- **FastAPI** as framework
- **Pydantic** for data validation
- **Server-Sent Events (SSE)** for streaming
- **Correlation IDs** for request tracking

## Base URL

```
http://localhost:8000/api/v1
```

When running via Docker Compose, the API is available at:
- **Internal (Docker network)**: `http://chat-api:8000/api/v1`
- **External**: `http://localhost:8000/api/v1`
- **Via Traefik**: `http://localhost/api/v1` (when configured)

## Authentication

⚠️ **Note**: Authentication is implemented via JWT tokens. All endpoints require a valid JWT token in the `Authorization: Bearer <token>` header, except for health check endpoints.

## Endpoints

### 1. Send Message (Streaming)

Sends a message and receives the AI response in real-time via Server-Sent Events.

**Endpoint**: `POST /chat/message/stream`

**Headers**:
```
Content-Type: application/json
Accept: text/event-stream
```

**Request Body**:
```json
{
  "message": "Hello, how are you?",
  "user_id": "user-123",
  "conversation_id": "conv-456",
  "model_id": "gpt-4"
}
```

**Fields**:
- `message` (required): Message content (1-10000 characters)
- `user_id` (optional): User identifier (default: extracted from JWT token)
- `conversation_id` (optional): Conversation ID to continue an existing conversation
- `model_id` (optional): Model ID to override the default

**Response**: Server-Sent Events (SSE)

**SSE Format**:
```
data: {"chunk": "Hello"}\n\n
data: {"chunk": ", "}\n\n
data: {"chunk": "I'm"}\n\n
data: {"chunk": " doing"}\n\n
data: {"chunk": " well"}\n\n
data: {"done": true}\n\n
```

**Error Events**:
```
data: {"error": "LLM service error", "type": "llm_error"}\n\n
data: {"error": "Database error", "type": "repository_error"}\n\n
data: {"error": "Unexpected error", "type": "unexpected_error"}\n\n
```

**Status Codes**:
- `200 OK`: Streaming started successfully
- `400 Bad Request`: Invalid data
- `401 Unauthorized`: Invalid or missing JWT token
- `500 Internal Server Error`: Error before streaming starts
- `503 Service Unavailable`: LLM service unavailable

**Usage Example (JavaScript)**:
```javascript
const eventSource = new EventSource('http://localhost:8000/api/v1/chat/message/stream', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: 'Hello, how are you?',
    user_id: 'user-123'
  })
});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.chunk) {
    console.log('Chunk:', data.chunk);
  } else if (data.done) {
    console.log('Streaming complete');
    eventSource.close();
  } else if (data.error) {
    console.error('Error:', data.error);
    eventSource.close();
  }
};
```

**Usage Example (cURL)**:
```bash
curl -N -X POST http://localhost:8000/api/v1/chat/message/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?",
    "user_id": "user-123"
  }'
```

### 2. Send Message (Non-Streaming)

Sends a message and receives the complete AI response.

**Endpoint**: `POST /chat/message`

**Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "message": "Hello, how are you?",
  "user_id": "user-123",
  "conversation_id": "conv-456",
  "model_id": "gpt-4"
}
```

**Response**:
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "response": "I'm doing well, thank you! How can I help you today?",
  "user_message": "Hello, how are you?",
  "assistant_message": "I'm doing well, thank you! How can I help you today?"
}
```

**Status Codes**:
- `200 OK`: Message processed successfully
- `400 Bad Request`: Invalid data or application error
- `401 Unauthorized`: Invalid or missing JWT token
- `500 Internal Server Error`: Repository error
- `503 Service Unavailable`: LLM service error

**Usage Example (cURL)**:
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?",
    "user_id": "user-123"
  }'
```

### 3. Health Check

Checks if the service is running.

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "ok"
}
```

**Status Codes**:
- `200 OK`: Service is running

### 4. Readiness Check

Checks if the service is ready to accept requests by testing connectivity with dependencies.

**Endpoint**: `GET /health/ready`

**Response** (Success):
```json
{
  "status": "ready",
  "checks": {
    "llm": {
      "status": "healthy",
      "response_received": true
    },
    "repository": {
      "status": "healthy"
    }
  }
}
```

**Response** (Failure):
```json
{
  "status": "not_ready",
  "checks": {
    "llm": {
      "status": "unhealthy",
      "error": "LLM provider timeout (no response within 5 seconds)"
    },
    "repository": {
      "status": "unhealthy",
      "error": "Database connection test failed"
    }
  }
}
```

**Status Codes**:
- `200 OK`: All components are healthy
- `503 Service Unavailable`: One or more components are unavailable

**Usage Example**:
```bash
curl http://localhost:8000/health/ready
```

### 5. List User Conversations

Returns a list of all conversations for the authenticated user.

**Endpoint**: `GET /conversations`

**Headers**:
```
Authorization: Bearer <JWT_TOKEN>
```

**Response**:
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user@example.com",
    "created_at": "2026-01-04T10:00:00Z",
    "updated_at": "2026-01-04T11:30:00Z",
    "message_count": 10,
    "last_message_preview": "Hello, how can I help you today?"
  }
]
```

**Status Codes**:
- `200 OK`: Conversation list returned successfully
- `401 Unauthorized`: Invalid or missing token
- `500 Internal Server Error`: Error fetching conversations

**Usage Example**:
```bash
curl -X GET http://localhost:8000/api/v1/conversations \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

### 6. Get Conversation by ID

Returns a specific conversation with full message history.

**Endpoint**: `GET /conversations/{conversation_id}`

**Headers**:
```
Authorization: Bearer <JWT_TOKEN>
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user@example.com",
  "created_at": "2026-01-04T10:00:00Z",
  "updated_at": "2026-01-04T11:30:00Z",
  "messages": [
    {
      "content": "Hello!",
      "role": "user",
      "timestamp": "2026-01-04T10:00:00Z"
    },
    {
      "content": "Hi! How can I help you?",
      "role": "assistant",
      "timestamp": "2026-01-04T10:00:05Z"
    }
  ]
}
```

**Status Codes**:
- `200 OK`: Conversation found and returned
- `401 Unauthorized`: Invalid or missing token
- `403 Forbidden`: Conversation does not belong to authenticated user
- `404 Not Found`: Conversation not found
- `500 Internal Server Error`: Error fetching conversation

**Usage Example**:
```bash
curl -X GET http://localhost:8000/api/v1/conversations/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

### 7. Delete Conversation

Permanently deletes a conversation and all its messages.

**Endpoint**: `DELETE /conversations/{conversation_id}`

**Headers**:
```
Authorization: Bearer <JWT_TOKEN>
```

**Response**:
```json
{
  "message": "Conversation deleted successfully",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Status Codes**:
- `200 OK`: Conversation deleted successfully
- `401 Unauthorized`: Invalid or missing token
- `403 Forbidden`: Conversation does not belong to authenticated user
- `404 Not Found`: Conversation not found
- `500 Internal Server Error`: Error deleting conversation

**Usage Example**:
```bash
curl -X DELETE http://localhost:8000/api/v1/conversations/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

## Data Models

### MessageRequestDTO

```typescript
{
  message: string;           // 1-10000 characters, required
  user_id?: string;          // 1-100 characters, optional (extracted from JWT if not provided)
  conversation_id?: string;  // 1-100 characters, optional
  model_id?: string;         // 1-200 characters, optional
}
```

**Validations**:
- `message`: Cannot be empty or only whitespace
- All optional fields have size limits

### MessageResponseDTO

```typescript
{
  conversation_id: string;  // Conversation UUID
  response: string;         // Complete AI response
  user_message: string;     // Original user message
  assistant_message: string; // AI response (same as response)
}
```

### ConversationSummaryDTO

```typescript
{
  id: string;                   // Conversation UUID
  user_id: string;              // User ID (email)
  created_at: string;           // ISO 8601 timestamp
  updated_at: string;           // ISO 8601 timestamp
  message_count: number;        // Number of messages in conversation
  last_message_preview: string; // Last message preview (100 chars)
}
```

### ConversationDTO

```typescript
{
  id: string;                   // Conversation UUID
  user_id: string;              // User ID (email)
  created_at: string;           // ISO 8601 timestamp
  updated_at: string;           // ISO 8601 timestamp
  messages: MessageDTO[];       // Array of messages
}
```

### MessageDTO

```typescript
{
  content: string;    // Message content
  role: string;       // 'user' or 'assistant'
  timestamp: string;  // ISO 8601 timestamp
}
```

## Status Codes

| Code | Meaning | When It Occurs |
|------|---------|----------------|
| `200` | OK | Successful request |
| `400` | Bad Request | Invalid data or application error |
| `401` | Unauthorized | Invalid or missing JWT token |
| `403` | Forbidden | User does not have access to resource |
| `404` | Not Found | Resource not found |
| `500` | Internal Server Error | Repository error or unexpected error |
| `503` | Service Unavailable | LLM service unavailable or infrastructure error |

## Usage Examples

### Example 1: New Conversation with Streaming

```bash
curl -N -X POST http://localhost:8000/api/v1/chat/message/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explique o que é machine learning",
    "user_id": "user-123"
  }'
```

### Example 2: Continue Existing Conversation

```bash
curl -N -X POST http://localhost:8000/api/v1/chat/message/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -d '{
    "message": "What about deep learning?",
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

### Example 3: Complete Response (Without Streaming)

```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -d '{
    "message": "What is the capital of Brazil?",
    "user_id": "user-123"
  }'
```

### Example 4: Using Python

```python
import requests
import json

# Streaming
response = requests.post(
    'http://localhost:8000/api/v1/chat/message/stream',
    json={
        'message': 'Hello, how are you?',
        'user_id': 'user-123'
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        data = json.loads(line.decode('utf-8').replace('data: ', ''))
        if 'chunk' in data:
            print(data['chunk'], end='', flush=True)
        elif 'done' in data:
            print('\nStreaming complete')
            break
        elif 'error' in data:
            print(f'\nError: {data["error"]}')
            break

# Não-streaming
response = requests.post(
    'http://localhost:8000/api/v1/chat/message',
    json={
        'message': 'Hello, how are you?',
        'user_id': 'user-123'
    }
)
print(response.json())
```

## Configuration

### Environment Variables

The API uses the following environment variables (configured in `docker-compose.yml`):

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql+asyncpg://user:pass@db:5432/chat_db` |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/0` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Jaeger endpoint for tracing | `http://jaeger:4317` |
| `LLM_PROVIDER` | LLM provider (`mock` or `openai`) | `mock` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-3.5-turbo` |
| `LLM_FALLBACK_ENABLED` | Enable automatic fallback | `true` |
| `LLM_STREAMING_TIMEOUT` | Streaming timeout (seconds) | `30.0` |
| `JWT_SECRET` | JWT secret for token validation | - |
| `API_PREFIX` | API prefix | `/api/v1` |
| `DEBUG` | Debug mode | `false` |

### Configuration via Docker Compose

Variables are configured in `docker-compose.yml`:

```yaml
chat-api:
  environment:
    - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/chat_db
    - REDIS_URL=redis://redis:6379/0
    - OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
    - LLM_PROVIDER=${LLM_PROVIDER:-mock}
    - OPENAI_API_KEY=${OPENAI_API_KEY:-}
```

## Observability

### Correlation IDs

All requests receive a unique Correlation ID in the `X-Correlation-ID` header. This ID is used to track requests across logs and traces.

**Header**:
```
X-Correlation-ID: 550e8400-e29b-41d4-a716-446655440000
```

### Logs

The API uses structured logging with the following fields:
- `correlation_id`: Unique request ID
- `timestamp`: ISO 8601 timestamp
- `level`: Log level (INFO, ERROR, etc.)
- `message`: Log message
- `context`: Additional context (user_id, conversation_id, etc.)

### Metrics

Metrics are collected by Prometheus (when the `/metrics` endpoint is implemented):
- Request count per endpoint
- Response time
- Error rate
- Resource usage

**Access**: http://localhost:9090

### Tracing

Distributed traces are sent to Jaeger:
- Request tracking across multiple services
- Latency and dependency visualization

**Access**: http://localhost:16686

### Dashboards

Grafana dashboards for metrics visualization:
- API performance
- Resource usage
- Error rate

**Access**: http://localhost:3000 (admin/admin)

## Interactive Documentation (Swagger/OpenAPI)

The API exposes interactive documentation via Swagger UI:

**URL**: http://localhost:8000/docs

**ReDoc**: http://localhost:8000/redoc

**OpenAPI JSON**: http://localhost:8000/openapi.json

## Limitations and Considerations

1. **Rate Limiting**: Not yet implemented (will be via Redis)
2. **Authentication**: Implemented via JWT tokens
3. **Model Validation**: The `model_id` field is accepted but not yet fully utilized
4. **Message Size**: Limited to 10,000 characters
5. **Streaming Timeout**: 30 seconds (configurable via `LLM_STREAMING_TIMEOUT`)

## Support and Contributing

For questions, bugs, or suggestions, see:
- [Project Documentation](../README.md)
- [ADRs (Architecture Decision Records)](./adr/README.md)
- [Architecture Diagrams](./diagrams/README.md)

