# Architecture Overview

┌─────────────────────────────────────────────┐
│         Frontend (Next.js)                   │  ← Interface do usuário
│         - React Components                   │
│         - SSE Client (EventSource)           │
│         - State Management                   │
└──────────────────┬──────────────────────────┘
                   │
                   │ HTTP/REST + SSE
                   │ (CORS enabled)
                   ▼
┌─────────────────────────────────────────────┐
│        API Layer (FastAPI)                  │  ← Entrada HTTP/SSE
│        - REST Endpoints                     │
│        - Streaming (SSE)                     │
│        - CORS Middleware                    │
│        - Correlation ID Middleware          │
├─────────────────────────────────────────────┤
│     Application Layer                       │  ← Orquestra casos de uso
│     - ProcessMessageUseCase                 │
│     - StreamMessageUseCase                  │
├─────────────────────────────────────────────┤
│        Domain Layer                         │  ← Regras puras
│        - Entities (Conversation)            │
│        - Value Objects (Message)            │
│        - Ports (LLMPort, RepositoryPort)   │
├─────────────────────────────────────────────┤
│    Infrastructure Layer                     │  ← AWS, DB, LLM
│    - LLM Providers (OpenAI)                │
│      • Fallback Chain                       │
│      • Streaming Support                    │
│    - Repository (InMemory)                 │
│    - Logging (Structured)                  │
└─────────────────────────────────────────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   OpenAI API  Database  (Future)
   (GPT-5/4/3)
