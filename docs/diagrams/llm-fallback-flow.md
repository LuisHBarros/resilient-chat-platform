# LLM Fallback Mechanism Flow

## Fallback Decision Tree

```
                    Start Streaming Request
                            │
                            ▼
                    ┌───────────────┐
                    │  Primary Model │
                    │ (gpt-5-nano)  │
                    └───────┬───────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Try Native Streaming   │
                └───────┬───────────────┘
                        │
            ┌───────────┴───────────┐
            │                       │
            ▼                       ▼
    ┌───────────────┐      ┌───────────────┐
    │   Success     │      │   Failure     │
    │  (chunks > 0) │      │ (no chunks)    │
    └───────┬───────┘      └───────┬───────┘
            │                      │
            │                      ▼
            │              ┌───────────────┐
            │              │ Try Simulated │
            │              │   Streaming   │
            │              └───────┬───────┘
            │                      │
            │          ┌───────────┴───────────┐
            │          │                       │
            │          ▼                       ▼
            │  ┌───────────────┐      ┌───────────────┐
            │  │   Success     │      │   Failure     │
            │  └───────┬───────┘      └───────┬───────┘
            │          │                      │
            │          │                      ▼
            │          │              ┌───────────────┐
            │          │              │ Mark Failed   │
            │          │              │ (cooldown)    │
            │          │              └───────┬───────┘
            │          │                      │
            └──────────┴──────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Fallback Model│
                    │ (gpt-5-mini)  │
                    └───────┬───────┘
                            │
                            ▼
                    [Repeat Process]
                            │
                            ▼
                    ┌───────────────┐
                    │ Fallback Model │
                    │   (gpt-4)      │
                    └───────┬───────┘
                            │
                            ▼
                    [Repeat Process]
                            │
                            ▼
                    ┌───────────────┐
                    │ Fallback Model │
                    │(gpt-3.5-turbo) │
                    └───────┬───────┘
                            │
                            ▼
                    [Repeat Process]
                            │
                            ▼
                    ┌───────────────┐
                    │  All Failed   │
                    │  Raise Error  │
                    └───────────────┘
```

## Detailed Fallback Flow

### Stage 1: Native Streaming Attempt

```
Model: gpt-5-nano
    │
    ├─> client.responses.stream()
    │       │
    │       ├─> Event: response.output_text.delta
    │       │       │
    │       │       ├─> Yield chunk
    │       │       │
    │       │       └─> chunks_yielded++
    │       │
    │       └─> Stream completes
    │               │
    │               ├─> chunks_yielded > 0
    │               │       │
    │               │       └─> ✅ SUCCESS - Return chunks
    │               │
    │               └─> chunks_yielded == 0
    │                       │
    │                       └─> ❌ FAILURE - Try Stage 2
```

### Stage 2: Simulated Streaming Fallback

```
Model: gpt-5-nano (same model, different method)
    │
    ├─> client.responses.create()  (non-streaming)
    │       │
    │       ├─> Extract response text
    │       │       │
    │       │       ├─> Empty response
    │       │       │       │
    │       │       │       └─> ❌ FAILURE - Try next model
    │       │       │
    │       │       └─> Has text
    │       │               │
    │       │               └─> Simulate streaming
    │       │                       │
    │       │                       ├─> Split into chunks (20 chars)
    │       │                       │
    │       │                       ├─> Yield chunk
    │       │                       │
    │       │                       ├─> Sleep (5ms)
    │       │                       │
    │       │                       └─> Repeat until done
    │       │                               │
    │       │                               └─> ✅ SUCCESS
    │       │
    │       └─> Exception
    │               │
    │               └─> ❌ FAILURE - Try next model
```

### Stage 3: Next Model in Chain

```
Check if model should be skipped (cooldown)
    │
    ├─> In cooldown (failed < 5 min ago)
    │       │
    │       └─> Skip model, try next
    │
    └─> Not in cooldown
            │
            └─> Try Stage 1 & 2 with next model
                    │
                    └─> Repeat until success or chain exhausted
```

## Cooldown Mechanism

```
Model Failure
    │
    ├─> Record failure timestamp
    │       │
    │       └─> failed_models[model] = current_time
    │
    └─> Next Request (same model)
            │
            ├─> Check cooldown
            │       │
            │       ├─> current_time - failed_models[model] < 300s
            │       │       │
            │       │       └─> ⏭️ SKIP (still in cooldown)
            │       │
            │       └─> current_time - failed_models[model] >= 300s
            │               │
            │               └─> ✅ TRY (cooldown expired)
```

## Configuration

### Default Fallback Chains

```python
{
    "gpt-5-nano": ["gpt-5-nano", "gpt-5-mini", "gpt-4", "gpt-3.5-turbo"],
    "gpt-5-mini": ["gpt-5-mini", "gpt-4", "gpt-3.5-turbo"],
    "gpt-4": ["gpt-4", "gpt-3.5-turbo"],
    "gpt-3.5-turbo": ["gpt-3.5-turbo"]  # No fallback
}
```

### Settings

```python
llm_fallback_enabled: bool = True
llm_fallback_chain: List[str] = ["gpt-5-nano", "gpt-5-mini", "gpt-4", "gpt-3.5-turbo"]
llm_streaming_timeout: float = 30.0
failure_cooldown: int = 300  # 5 minutes
```

## Error Scenarios

### Scenario 1: Empty Streaming Response
```
gpt-5-nano → Native streaming → 0 chunks
    │
    └─> Simulated streaming → Empty response
            │
            └─> gpt-5-mini → Native streaming → Success ✅
```

### Scenario 2: API Error
```
gpt-5-nano → Native streaming → API Error (400)
    │
    └─> Simulated streaming → API Error (400)
            │
            └─> gpt-5-mini → Native streaming → Success ✅
```

### Scenario 3: Network Timeout
```
gpt-5-nano → Native streaming → Timeout
    │
    └─> Simulated streaming → Timeout
            │
            └─> gpt-4 → Native streaming → Success ✅
```

### Scenario 4: All Models Fail
```
gpt-5-nano → Failure
    │
gpt-5-mini → Failure
    │
gpt-4 → Failure
    │
gpt-3.5-turbo → Failure
    │
    └─> Raise RuntimeError("All models failed")
```

## Performance Considerations

- **Cooldown**: Prevents repeated failures on same model
- **Optimized Chain**: Only includes necessary fallbacks
- **Fast Simulated Streaming**: 20-char chunks, 5ms sleep
- **Logging**: All attempts logged with correlation ID
- **Metrics**: Track which models succeed/fail (future enhancement)

## Logging Example

```
INFO: Attempting streaming with model: gpt-5-nano
WARNING: Native streaming failed with gpt-5-nano: returned stream with no chunks
WARNING: Falling back to fast simulated streaming...
WARNING: Fallback simulated streaming failed for gpt-5-nano: returned empty response
INFO: Attempting streaming with model: gpt-5-mini
INFO: Streaming successful with gpt-5-mini: 45 chunks
```

