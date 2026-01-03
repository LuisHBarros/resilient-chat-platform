# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) documenting important architectural decisions made in this project.

## What are ADRs?

ADRs are documents that capture important architectural decisions along with their context and consequences. They help:
- Document why decisions were made
- Provide context for future developers
- Track the evolution of the architecture
- Avoid repeating discussions

## ADR Index

- [ADR-0001: Clean Architecture](./0001-clean-architecture.md) - Why we chose Clean Architecture
- [ADR-0002: Multiple LLM Providers](./0002-multiple-llm-providers.md) - Why we support multiple LLM providers
- [ADR-0003: Structured Logging](./0003-structured-logging.md) - Why we use structured logging with correlation IDs
- [ADR-0004: Unit Testing with Fakes](./0004-unit-testing-with-fakes.md) - Why we use fakes for unit testing
- [ADR-0005: Streaming with Server-Sent Events](./0005-streaming-with-sse.md) - Why we use SSE for real-time streaming
- [ADR-0006: LLM Fallback Mechanism](./0006-llm-fallback-mechanism.md) - Why we implement automatic model fallback
- [ADR-0007: OpenAI API Responses vs Chat Completions](./0007-openai-api-responses-vs-chat-completions.md) - How we handle different OpenAI APIs
- [ADR-0008: CORS Configuration](./0008-cors-configuration.md) - Why we configure CORS for frontend-backend communication
- [ADR-0009: Error Handling and Resilience](./0009-error-handling-and-resilience.md) - How we handle errors and ensure system resilience

## Format

Each ADR follows this structure:
- **Status**: Proposed, Accepted, Rejected, Deprecated, Superseded
- **Context**: The situation that led to this decision
- **Decision**: What we decided to do
- **Consequences**: Positive and negative outcomes
- **Alternatives Considered**: Other options we evaluated

## References

- [ADR Template](https://adr.github.io/)
- [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)

