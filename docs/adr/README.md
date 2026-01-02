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

