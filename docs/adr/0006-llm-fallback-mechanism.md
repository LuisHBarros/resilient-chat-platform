# ADR-0006: LLM Fallback Mechanism

## Status
Accepted

## Context
LLM providers can fail for various reasons:
- API rate limits
- Model unavailability
- Network issues
- Model-specific errors (e.g., GPT-5 Nano may return empty responses)
- Cost optimization (use cheaper models when possible)

We need resilience to ensure:
- Users always get a response (when possible)
- System degrades gracefully
- No single point of failure
- Automatic recovery without user intervention

## Decision
We implemented a configurable fallback chain mechanism in `OpenAIProvider`:

1. **Fallback Chain**: Ordered list of models to try (e.g., `gpt-5-nano` → `gpt-5-mini` → `gpt-4` → `gpt-3.5-turbo`)
2. **Two-Stage Fallback**: 
   - First: Try native streaming
   - Second: If streaming fails, try non-streaming with simulated streaming
3. **Failure Cooldown**: Models that fail are temporarily skipped (5-minute cooldown)
4. **Configuration**: Fallback chain configurable via `settings.llm_fallback_chain`
5. **Automatic**: No user intervention required

### Architecture:
```
Primary Model (gpt-5-nano)
    |
    |-- Try native streaming
    |   |
    |   |-- Success → Return chunks
    |   |
    |   |-- Failure → Try simulated streaming
    |       |
    |       |-- Success → Return chunks
    |       |
    |       |-- Failure → Next model in chain
    |
Fallback Model 1 (gpt-5-mini)
    |-- [Same process]
    |
Fallback Model 2 (gpt-4)
    |-- [Same process]
    |
Fallback Model 3 (gpt-3.5-turbo)
    |-- [Same process]
    |
All Failed → Raise error
```

### Implementation Details:
- `_get_fallback_chain()`: Defines default chains per model
- `_should_skip_model()`: Checks cooldown for failed models
- `_mark_model_failed()`: Records failure timestamp
- `generate_stream()`: Orchestrates fallback logic
- `_try_stream_with_model()`: Attempts native streaming
- `_generate_and_simulate_stream()`: Fallback with simulated streaming

## Consequences

### Positive:
- ✅ High availability (automatic failover)
- ✅ Graceful degradation (use cheaper models when expensive ones fail)
- ✅ No user-visible errors (seamless fallback)
- ✅ Cost optimization (can start with cheaper models)
- ✅ Resilient to transient failures
- ✅ Configurable per environment

### Negative:
- ⚠️ Increased latency if fallback is triggered
- ⚠️ May use more expensive models if cheaper ones fail
- ⚠️ Complexity in error handling
- ⚠️ Need to maintain fallback chains
- ⚠️ Simulated streaming is not true streaming (but acceptable fallback)

## Configuration

```python
# settings.py
llm_fallback_enabled: bool = True
llm_fallback_chain: List[str] = ["gpt-5-nano", "gpt-5-mini", "gpt-4", "gpt-3.5-turbo"]
llm_streaming_timeout: float = 30.0
```

## Failure Scenarios Handled

1. **Empty Streaming Response**: Falls back to simulated streaming, then next model
2. **API Errors**: Catches exceptions, tries next model
3. **Network Timeouts**: Handled by exception, tries next model
4. **Model Unavailability**: Detected by empty response, tries next model
5. **Rate Limits**: Handled by exception, tries next model

## Alternatives Considered

1. **No Fallback**: Simple but poor user experience on failures
2. **Manual Retry**: Requires user intervention, poor UX
3. **Circuit Breaker**: Good for preventing cascading failures, but we also need fallback
4. **Load Balancing**: Doesn't help with model-specific failures
5. **Single Fallback**: Less resilient than chain

## Future Enhancements

- Add metrics for fallback usage
- Add alerting when fallbacks are frequently triggered
- Add adaptive fallback (learn which models work best)
- Add cost tracking per model
- Add health checks for models

## References
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Fallback Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)

