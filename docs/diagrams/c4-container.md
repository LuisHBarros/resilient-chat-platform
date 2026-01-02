# C4 Model - Container Diagram

## Container Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AI Chat Platform                             │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    API Layer (FastAPI)                        │  │
│  │  - Routes & Endpoints                                          │  │
│  │  - DTOs (Request/Response)                                     │  │
│  │  - Middleware (Correlation ID)                                │  │
│  │  - Dependency Injection                                       │  │
│  └──────────────┬───────────────────────────────────────────────┘  │
│                 │                                                    │
│                 │ Uses                                               │
│                 ▼                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Application Layer                                 │  │
│  │  - Use Cases (ProcessMessageUseCase)                          │  │
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
│  │  │ - Bedrock    │  │              │  │   Logger      │       │  │
│  │  │ - Mock       │  │              │  │               │       │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘       │  │
│  │  ┌──────────────┐                                             │  │
│  │  │  Config      │                                             │  │
│  │  │  Settings    │                                             │  │
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
- Validate input via DTOs
- Route requests to use cases
- Handle exceptions and return appropriate HTTP status codes
- Add correlation IDs via middleware

**Key Components**:
- `app/api/routes/` - API endpoints
- `app/api/dto/` - Data Transfer Objects
- `app/api/middleware/` - Request middleware
- `app/api/dependencies.py` - FastAPI dependency injection

### 2. Application Layer
**Technology**: Python  
**Responsibilities**:
- Orchestrate use cases
- Coordinate domain entities and value objects
- Handle application-level business logic
- Manage transaction boundaries

**Key Components**:
- `app/application/use_cases/` - Use case implementations
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

**Key Components**:
- `app/infrastructure/llm/` - LLM provider implementations
- `app/infrastructure/persistence/` - Repository implementations
- `app/infrastructure/logging/` - Logging implementations
- `app/infrastructure/config/` - Configuration management

### 5. Composition Root (bootstrap.py)
**Technology**: Python  
**Responsibilities**:
- Compose all dependencies
- Create object graph
- Manage dependency lifecycle
- Centralize dependency resolution

## Data Flow

1. **Request** → API Layer receives HTTP request
2. **Validation** → DTO validates input
3. **Dependency Injection** → FastAPI injects use case via composition root
4. **Use Case Execution** → Application layer orchestrates business logic
5. **Domain Logic** → Domain entities enforce business rules
6. **Infrastructure** → Adapters call external services (LLM, DB)
7. **Response** → Result flows back through layers to API response

## Technology Choices

- **FastAPI**: Modern, fast Python web framework with automatic OpenAPI docs
- **Pydantic**: Data validation and serialization
- **Protocols**: Python's structural typing for ports
- **Dependency Injection**: Manual DI via composition root (no framework needed)

