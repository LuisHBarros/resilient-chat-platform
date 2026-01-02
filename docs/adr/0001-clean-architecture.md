# ADR-0001: Clean Architecture

## Status
Accepted

## Context
We needed to structure our application in a way that:
- Keeps business logic independent of frameworks and external services
- Makes the codebase testable and maintainable
- Allows easy swapping of implementations (e.g., different LLM providers, databases)
- Follows SOLID principles, especially Dependency Inversion

## Decision
We adopted Clean Architecture (also known as Hexagonal Architecture or Ports & Adapters) with the following structure:

```
app/
├── api/              # Framework layer (FastAPI)
├── application/      # Use cases (application logic)
├── domain/           # Business logic, entities, ports
└── infrastructure/   # External adapters (LLM, DB, logging)
```

### Key Principles:
1. **Dependency Rule**: Dependencies point inward
   - API depends on Application
   - Application depends on Domain
   - Infrastructure depends on Domain (implements ports)

2. **Ports & Adapters**: Domain defines ports (interfaces), Infrastructure implements them

3. **Use Cases**: Application layer contains use cases that orchestrate domain logic

## Consequences

### Positive:
- ✅ Business logic is independent of frameworks
- ✅ Easy to test (use fakes that implement ports)
- ✅ Easy to swap implementations (e.g., switch LLM providers)
- ✅ Clear separation of concerns
- ✅ High cohesion, low coupling

### Negative:
- ⚠️ More files and structure (but better organized)
- ⚠️ Requires discipline to maintain boundaries
- ⚠️ Slight learning curve for new developers

## Alternatives Considered

1. **MVC Pattern**: Too coupled to frameworks, harder to test
2. **Layered Architecture**: Still allows dependencies on infrastructure
3. **Onion Architecture**: Similar to Clean Architecture, but we chose Clean Architecture for its simplicity

## References
- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Hexagonal Architecture by Alistair Cockburn](https://alistair.cockburn.us/hexagonal-architecture/)

