# ADR-0004: Unit Testing with Fakes

## Status
Accepted

## Context
We need to test our use cases (application layer) without:
- Depending on infrastructure implementations
- Making external API calls (slow, unreliable)
- Setting up databases or other external services
- Breaking when infrastructure changes

Traditional mocks can create tight coupling to implementations.

## Decision
We use **Fakes** that implement domain ports for unit testing:

1. **Fake Implementations**: `FakeLLM`, `FakeRepository` in `tests/unit/fakes.py`
2. **Port Compliance**: Fakes implement domain ports (`LLMPort`, `RepositoryPort`)
3. **Test Isolation**: Tests depend only on domain ports, not infrastructure
4. **Fast & Reliable**: No external dependencies, tests run in milliseconds

### Example:
```python
class FakeLLM(LLMPort):
    async def generate(self, message: str) -> str:
        return "ok"

# Test
async def test_process_message():
    use_case = ProcessMessageUseCase(FakeLLM(), FakeRepository())
    result = await use_case.execute("hi")
    assert result["response"] == "ok"
```

## Consequences

### Positive:
- ✅ Tests are fast (no I/O)
- ✅ Tests are reliable (no network calls)
- ✅ Tests verify architecture (use case depends only on ports)
- ✅ Easy to test edge cases (errors, timeouts, etc.)
- ✅ No test infrastructure needed

### Negative:
- ⚠️ Need to maintain fake implementations
- ⚠️ Fakes may not perfectly match real implementations (but that's OK for unit tests)
- ⚠️ Still need integration tests for real implementations

## Testing Strategy

1. **Unit Tests**: Use fakes, test use cases in isolation
2. **Integration Tests**: Use real implementations, test full flow
3. **Contract Tests**: Verify fakes match real implementations (optional)

## Alternatives Considered

1. **Mocks**: Can create tight coupling to implementations
2. **Stubs**: Similar to fakes, but fakes are more complete
3. **Test Doubles**: Generic term, fakes are a specific type
4. **Real Implementations**: Too slow and unreliable for unit tests

## References
- [Test Doubles: Mocks, Fakes, Stubs and Spies](https://martinfowler.com/bliki/TestDouble.html)
- [Growing Object-Oriented Software, Guided by Tests](https://www.growing-object-oriented-software.com/)

