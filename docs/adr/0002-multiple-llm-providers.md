# ADR-0002: Multiple LLM Providers

## Status
Accepted

## Context
We need to support multiple Large Language Model (LLM) providers because:
- Different providers have different capabilities and costs
- We may need to switch providers based on availability or cost
- Some providers may be better for specific use cases
- We want to avoid vendor lock-in

## Decision
We implemented a provider-agnostic architecture using the Port pattern:

1. **Domain Port**: `LLMPort` protocol defines the interface
2. **Multiple Implementations**: 
   - `OpenAIProvider` (OpenAI API)
   - `MockProvider` (for testing/development)
3. **Factory Pattern**: `create_llm_provider()` in infrastructure layer
4. **Configuration-based**: Provider selected via `LLM_PROVIDER` environment variable

### Architecture:
```
Domain (Port)          Infrastructure (Adapters)
┌─────────────┐       ┌─────────────────┐
│  LLMPort    │◄──────│ OpenAIProvider │
│  Protocol   │       │ MockProvider   │
└─────────────┘       └─────────────────┘
```

## Consequences

### Positive:
- ✅ Easy to add new providers (just implement `LLMPort`)
- ✅ No vendor lock-in
- ✅ Can switch providers via configuration
- ✅ Testable with `MockProvider` or fakes
- ✅ Business logic doesn't know which provider is used

### Negative:
- ⚠️ Each provider may have different capabilities (handled in implementation)
- ⚠️ Need to maintain multiple implementations
- ⚠️ Configuration complexity increases

## Implementation Details

- Factory function in `infrastructure/llm/factory.py`
- All providers implement `LLMPort` protocol
- Use case depends only on `LLMPort`, not concrete implementations
- Configuration via `settings.llm_provider`

## Alternatives Considered

1. **Single Provider**: Simpler, but vendor lock-in
2. **Adapter Pattern**: Similar approach, but Protocol is more Pythonic
3. **Strategy Pattern**: Could work, but Port pattern is cleaner for Clean Architecture

## References
- [Protocols in Python](https://docs.python.org/3/library/typing.html#typing.Protocol)
- [Factory Pattern](https://refactoring.guru/design-patterns/factory-method)

