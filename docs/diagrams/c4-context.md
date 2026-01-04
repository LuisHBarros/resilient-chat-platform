# C4 Model - Context Diagram

## System Context

```
┌─────────────────────────────────────────────────────────────┐
│                        Users                                 │
│              (Web Browser / API Consumers)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ HTTP/REST + SSE
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  AI Chat Platform                            │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              FastAPI Backend                            │  │
│  │  - REST API Endpoints                                   │  │
│  │  - Streaming (Server-Sent Events)                       │  │
│  │  - CORS Middleware                                      │  │
│  │  - Request/Response Handling                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Next.js Frontend                          │  │
│  │  - React Components                                    │  │
│  │  - SSE Client (EventSource)                            │  │
│  │  - State Management                                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   OpenAI    │ │   Database  │ │   (Future)  │
│     API     │ │  (Future)  │ │             │
│ - GPT-5     │ │             │ │             │
│ - GPT-4     │ │             │ │             │
│ - GPT-3.5   │ │             │ │             │
└─────────────┘ └─────────────┘ └─────────────┘
```

## Description

The **AI Chat Platform** is a full-stack application that provides conversational AI capabilities. It consists of:

1. **Next.js Frontend**: Modern React-based web application with real-time streaming support
2. **FastAPI Backend**: RESTful API with Server-Sent Events (SSE) for streaming responses

Users interact with the platform through a web interface that provides a ChatGPT-like experience with real-time streaming responses.

### External Systems

1. **Users**: Web browser users and API consumers
2. **OpenAI API**: External LLM provider with multiple models (GPT-5, GPT-4, GPT-3.5)
3. **Database**: Future persistence layer (currently using in-memory storage)

### Key Characteristics

- **Real-time Streaming**: Server-Sent Events (SSE) for ChatGPT-like UX
- **Resilient**: Automatic fallback between LLM models
- **Provider-agnostic**: Can use different LLM providers
- **Scalable**: Designed to handle multiple concurrent requests
- **Observable**: Structured logging with correlation IDs
- **CORS-enabled**: Frontend-backend communication configured

