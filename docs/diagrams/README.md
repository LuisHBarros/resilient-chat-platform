# Architecture Diagrams

This directory contains architecture diagrams documenting the system design and data flows.

## Diagram Index

### C4 Model Diagrams

- **[C4 Context Diagram](./c4-context.md)** - System context showing external systems and users
  - Shows frontend (Next.js), backend (FastAPI), and external LLM providers
  - Documents CORS configuration and streaming support

- **[C4 Container Diagram](./c4-container.md)** - Container-level architecture
  - Shows API Layer, Application Layer, Domain Layer, Infrastructure Layer
  - Documents Clean Architecture structure
  - Includes streaming endpoints and fallback mechanisms

### Flow Diagrams

- **[Message Processing Flow](./flow-message-processing.md)** - Non-streaming message processing
  - Sequence diagram for traditional request-response flow
  - Shows interaction between layers
  - Documents error handling

- **[Streaming Message Processing Flow](./flow-streaming.md)** - Streaming with Server-Sent Events (SSE)
  - Detailed sequence diagram for streaming flow
  - Shows fallback mechanism in action
  - Documents SSE event format
  - Includes frontend integration examples

- **[LLM Fallback Flow](./llm-fallback-flow.md)** - Fallback mechanism decision tree
  - Visual representation of fallback chain
  - Shows native streaming → simulated streaming → next model flow
  - Documents cooldown mechanism
  - Includes error scenarios

### Architecture Overview

- **[Architecture Overview](./architecture.md)** - High-level architecture diagram
  - Simple layered architecture view
  - Shows frontend-backend communication
  - Documents all layers and their responsibilities

## Diagram Conventions

### Symbols
- `┌─┐` - Container/Component
- `│` - Vertical flow
- `├─` - Branch/Decision
- `▼` - Data flow down
- `▲` - Data flow up
- `─→` - Request/Message
- `←─` - Response/Reply

### Colors (when rendered)
- **Blue**: External systems
- **Green**: Internal components
- **Yellow**: Data/State
- **Red**: Errors/Exceptions

## Key Concepts Documented

### Streaming Architecture
- Server-Sent Events (SSE) for real-time responses
- StreamingResponse in FastAPI
- Chunk accumulation with StringIO
- Response length limits

### Fallback Mechanism
- Automatic model fallback chain
- Two-stage fallback (native → simulated streaming)
- Failure cooldown mechanism
- Configurable fallback chains

### Clean Architecture
- Layer separation (API → Application → Domain → Infrastructure)
- Dependency inversion (ports & adapters)
- Use case orchestration
- Domain-driven design

### Error Handling
- Domain exceptions
- Application exceptions
- Infrastructure exceptions
- SSE error events
- Error state persistence

## Related Documentation

- [Architecture Decision Records (ADRs)](../adr/) - Detailed architectural decisions
- [API Documentation](../../app/api/) - API endpoint documentation
- [Domain Model](../../app/domain/) - Domain entities and value objects

## Updating Diagrams

When updating diagrams:
1. Keep ASCII art readable (use consistent spacing)
2. Update related diagrams if changes affect multiple views
3. Add notes explaining complex flows
4. Include error scenarios when relevant
5. Document configuration options

## Tools for Rendering

These diagrams are in ASCII format but can be rendered with:
- [Mermaid](https://mermaid.js.org/) - Convert to visual diagrams
- [PlantUML](https://plantuml.com/) - Generate UML diagrams
- [ASCII Flow](https://asciiflow.com/) - Edit ASCII diagrams
- [Draw.io](https://app.diagrams.net/) - Visual diagram editor

## Future Enhancements

- Add component diagrams (C4 Level 3)
- Add deployment diagrams
- Add sequence diagrams for specific use cases
- Add state diagrams for conversation lifecycle
- Convert to Mermaid format for better rendering

