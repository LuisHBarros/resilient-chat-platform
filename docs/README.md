# Documentation

This directory contains technical documentation for the AI Chat Platform.

## Structure

```
docs/
├── adr/                    # Architecture Decision Records
│   ├── README.md          # ADR index and guide
│   ├── 0001-clean-architecture.md
│   ├── 0002-multiple-llm-providers.md
│   ├── 0003-structured-logging.md
│   └── 0004-unit-testing-with-fakes.md
│
└── diagrams/              # Architecture diagrams
    ├── c4-context.md      # C4 Context diagram
    ├── c4-container.md    # C4 Container diagram
    └── flow-message-processing.md  # Sequence diagram
```

## Documentation Types

### Architecture Decision Records (ADRs)
ADRs document important architectural decisions, their context, and consequences. See [adr/README.md](./adr/README.md) for details.

### Diagrams

#### C4 Model
- **Context Diagram**: High-level system context and external dependencies
- **Container Diagram**: Application containers and their relationships

#### Flow Diagrams
- **Message Processing Flow**: Sequence diagram showing how messages are processed

## Quick Links

- [API Documentation](./API.md) - Documentação completa da API REST
- [Architecture Decisions](./adr/README.md)
- [System Context](./diagrams/c4-context.md)
- [Container Architecture](./diagrams/c4-container.md)
- [Message Processing Flow](./diagrams/flow-message-processing.md)

## Contributing

When adding new documentation:
1. Follow existing patterns and formats
2. Keep diagrams up to date with code changes
3. Document decisions in ADRs when making architectural changes
4. Update this README when adding new documentation

