# C4 Model - Container Diagram

## Container Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AI Chat Platform                             │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    API Layer (FastAPI)                        │  │
│  │  - Routes & Endpoints                                          │  │
│  │  - Streaming Endpoints (SSE)                                  │  │
│  │  - DTOs (Request/Response)                                     │  │
│  │  - Middleware (Correlation ID, CORS)                          │  │
│  │  - Dependency Injection                                       │  │
│  └──────────────┬───────────────────────────────────────────────┘  │
│                 │                                                    │
│                 │ Uses                                               │
│                 ▼                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Application Layer                                 │  │
│  │  - Use Cases                                                  │  │
│  │    • ProcessMessageUseCase (non-streaming)                    │  │
│  │    • StreamMessageUseCase (SSE streaming)                     │  │
│  │  - Application Services                                       │  │
│  │  - Application Exceptions                                     │  │
│  └──────────────┬───────────────────────────────────────────────┘  │
│                 │                                                    │
│                 │ Depends on                                         │
│                 ▼                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                  Domain Layer                                  │  │
│  │  - Entities (Conversation)                                     │  │
│  │  - Value Objects (Message)                                     │  │
│  │  - Ports (LLMPort, RepositoryPort, LoggerPort)               │  │
│  │  - Domain Exceptions                                          │  │
│  └──────────────┬───────────────────────────────────────────────┘  │
│                 │                                                    │
│                 │ Implemented by                                     │
│                 ▼                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Infrastructure Layer                              │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │  │
│  │  │ LLM Adapters │  │ Repository   │  │   Logging     │       │  │
│  │  │ - OpenAI     │  │ - InMemory   │  │ - Structured   │       │  │
│  │  │   • GPT-5    │  │              │  │   Logger      │       │  │
│  │  │   • GPT-4    │  │              │  │               │       │  │
│  │  │   • Fallback │  │              │  │               │       │  │
│  │  │ - Bedrock    │  │              │  │               │       │  │
│  │  │ - Mock       │  │              │  │               │       │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘       │  │
│  │  ┌──────────────┐                                             │  │
│  │  │  Config      │                                             │  │
│  │  │  Settings    │                                             │  │
│  │  │  - CORS      │                                             │  │
│  │  │  - Fallback  │                                             │  │
│  │  └──────────────┘                                             │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Composition Root (bootstrap.py)                  │  │
│  │  - Wires all dependencies                                     │  │
│  │  - Creates object graph                                       │  │
│  │  - Dependency injection                                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Container Descriptions

### 1. API Layer (FastAPI)
**Technology**: FastAPI, Python  
**Responsibilities**:
- Handle HTTP requests/responses
- Handle streaming responses (Server-Sent Events)
- Validate input via DTOs
- Route requests to use cases
- Handle exceptions and return appropriate HTTP status codes
- Add correlation IDs via middleware
- Configure CORS for frontend communication

**Key Components**:
- `app/api/routes/chat_routes.py` - Non-streaming endpoints
- `app/api/routes/chat_stream_routes.py` - Streaming endpoints (SSE)
- `app/api/dto/` - Data Transfer Objects
- `app/api/middleware/` - Request middleware (Correlation ID, CORS)
- `app/api/dependencies.py` - FastAPI dependency injection
- `app/main.py` - CORS configuration

### 2. Application Layer
**Technology**: Python  
**Responsibilities**:
- Orchestrate use cases
- Coordinate domain entities and value objects
- Handle application-level business logic
- Manage transaction boundaries
- Stream responses in real-time

**Key Components**:
- `app/application/use_cases/process_message.py` - Non-streaming message processing
- `app/application/use_cases/stream_message.py` - Streaming message processing (SSE)
- `app/application/exceptions.py` - Application exceptions

### 3. Domain Layer
**Technology**: Python  
**Responsibilities**:
- Define business entities and value objects
- Define ports (interfaces) for external dependencies
- Enforce business rules and invariants
- Domain exceptions

**Key Components**:
- `app/domain/entities/` - Domain entities
- `app/domain/value_objects/` - Value objects
- `app/domain/ports/` - Port definitions (Protocols)
- `app/domain/exceptions.py` - Domain exceptions

### 4. Infrastructure Layer
**Technology**: Python, boto3, openai  
**Responsibilities**:
- Implement domain ports
- Handle external service integrations
- Manage configuration
- Provide logging and observability
- Implement fallback mechanisms
- Handle different OpenAI API formats (responses vs chat.completions)

**Key Components**:
- `app/infrastructure/llm/openai_provider.py` - OpenAI provider with fallback chain
- `app/infrastructure/llm/bedrock_provider.py` - AWS Bedrock provider
- `app/infrastructure/llm/mock_provider.py` - Mock provider for testing
- `app/infrastructure/persistence/` - Repository implementations
- `app/infrastructure/logging/` - Logging implementations
- `app/infrastructure/config/` - Configuration management (CORS, fallback, etc.)

### 5. Composition Root (bootstrap.py)
**Technology**: Python  
**Responsibilities**:
- Compose all dependencies
- Create object graph
- Manage dependency lifecycle
- Centralize dependency resolution

## Data Flow

### Non-Streaming Flow:
1. **Request** → API Layer receives HTTP request
2. **Validation** → DTO validates input
3. **Dependency Injection** → FastAPI injects use case via composition root
4. **Use Case Execution** → Application layer orchestrates business logic
5. **Domain Logic** → Domain entities enforce business rules
6. **Infrastructure** → Adapters call external services (LLM, DB)
7. **Response** → Result flows back through layers to API response

### Streaming Flow (SSE):
1. **Request** → API Layer receives HTTP POST to `/message/stream`
2. **Validation** → DTO validates input
3. **Streaming Response** → FastAPI creates `StreamingResponse` with SSE format
4. **Use Case Execution** → `StreamMessageUseCase` yields chunks as they're generated
5. **LLM Streaming** → LLM provider streams response chunks (with fallback if needed)
6. **SSE Events** → Each chunk sent as `data: {json}\n\n`
7. **Persistence** → User message saved immediately, assistant message saved after streaming

## Technology Choices

- **FastAPI**: Modern, fast Python web framework with automatic OpenAPI docs
- **Pydantic**: Data validation and serialization
- **Protocols**: Python's structural typing for ports
- **Dependency Injection**: Manual DI via composition root (no framework needed)

