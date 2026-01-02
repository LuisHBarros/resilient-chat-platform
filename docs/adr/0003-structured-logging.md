# ADR-0003: Structured Logging with Correlation ID

## Status
Accepted

## Context
We need observability in production to:
- Debug issues across distributed systems
- Track requests through the system
- Monitor performance and errors
- Comply with audit requirements

Traditional logging (plain text) is hard to parse and analyze at scale.

## Decision
We implemented structured logging with correlation IDs:

1. **Logger Port**: `LoggerPort` protocol in domain layer
2. **Structured Logger**: JSON-formatted logs in infrastructure
3. **Correlation ID**: Middleware adds unique ID to each request
4. **Context Propagation**: Logger can add context (user_id, correlation_id, etc.)

### Implementation:
- `LoggerPort` protocol in `domain/ports/logger_port.py`
- `StructuredLogger` in `infrastructure/logging/structured_logger.py`
- `CorrelationIDMiddleware` in `api/middleware/correlation.py`
- Logs output as JSON for easy parsing

## Consequences

### Positive:
- ✅ Easy to parse and analyze logs (JSON format)
- ✅ Correlation IDs enable request tracing
- ✅ Can add context without changing code
- ✅ Domain layer doesn't depend on logging implementation
- ✅ Testable with `NullLogger` fake

### Negative:
- ⚠️ Slightly more verbose than plain logging
- ⚠️ Need log aggregation tool (e.g., ELK, CloudWatch) for production
- ⚠️ JSON logs are harder to read in development (can add pretty formatter)

## Example Log Output

```json
{
  "timestamp": "2024-01-15T10:30:00.123456",
  "level": "INFO",
  "message": "Processing message",
  "correlation_id": "abc-123-def",
  "user_id": "user-456",
  "conversation_id": "conv-789",
  "message_length": 42
}
```

## Alternatives Considered

1. **Plain Text Logging**: Simple, but hard to parse
2. **Third-party Libraries** (e.g., structlog): Good, but adds dependency
3. **Application Insights/CloudWatch**: Vendor-specific, less portable

## Future Enhancements
- Add distributed tracing (OpenTelemetry)
- Add metrics collection
- Add log levels configuration
- Add pretty formatter for development

## References
- [Structured Logging Best Practices](https://www.structlog.org/en/stable/why.html)
- [Correlation IDs Pattern](https://microservices.io/patterns/observability/correlation-id.html)

