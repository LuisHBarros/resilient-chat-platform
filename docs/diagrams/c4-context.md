# C4 Model - Context Diagram

## System Context

```
┌─────────────────────────────────────────────────────────────┐
│                        Users                                 │
│                   (API Consumers)                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ HTTP/REST
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  AI Chat Platform                            │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              FastAPI Application                      │  │
│  │  - REST API Endpoints                                 │  │
│  │  - Request/Response Handling                          │  │
│  │  - Authentication & Authorization                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   OpenAI    │ │ AWS Bedrock │ │   Database  │
│     API     │ │     API     │ │  (Future)   │
└─────────────┘ └─────────────┘ └─────────────┘
```

## Description

The **AI Chat Platform** is a backend service that provides conversational AI capabilities through a REST API. Users interact with the platform by sending messages and receiving AI-generated responses.

### External Systems

1. **Users**: API consumers who send messages and receive responses
2. **OpenAI API**: External LLM provider (optional, configured via settings)
3. **AWS Bedrock API**: External LLM provider (optional, configured via settings)
4. **Database**: Future persistence layer (currently using in-memory storage)

### Key Characteristics

- **Stateless**: Each request is independent
- **Provider-agnostic**: Can use different LLM providers
- **Scalable**: Designed to handle multiple concurrent requests
- **Observable**: Structured logging with correlation IDs

