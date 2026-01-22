# 🛡️ Resilient Chat Platform

> Enterprise-grade conversational AI backend with focus on **resilience**, **observability**, and **clean architecture patterns**.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 **Why This Project Exists**

I built this platform to explore advanced backend architecture patterns applicable to **mission-critical distributed systems** - such as logistics platforms, real-time tracking, and integrations with multiple external partners.

The challenges solved here are directly transferable to scenarios where **high availability**, **end-to-end observability**, and **graceful degradation** are non-negotiable requirements.

---

## ✨ **Technical Highlights**

### 🛡️ **Resilience First**
- **Circuit Breaker Pattern**: Automatic degradation between LLM providers (GPT-5 → GPT-4 → GPT-3.5)
- **Fallback Chain**: Ensures 99.9% availability even with provider failures
- **Retry Logic**: Automatic retries with exponential backoff
- **Timeout Management**: Latency control for each external call

### 📊 **Complete Observability**
- **OpenTelemetry**: Distributed instrumentation across the entire stack
- **Jaeger**: End-to-end trace visualization (API → Database → LLM)
- **Prometheus**: Performance metrics collection
- **Grafana**: Dashboards for latency and bottleneck analysis
- **Structured Logging**: Correlation IDs for request tracking

### 🏗️ **Clean Architecture**
- **Hexagonal Architecture (Ports & Adapters)**: Total decoupling between domain and infrastructure
- **Clean Architecture**: Rigorous layer separation (Entities → Use Cases → Adapters)
- **Domain-Driven Design (DDD)**: Rich domain modeling
- **Event-Driven**: Real-time event streaming with consistency guarantees

### ⚡ **Performance & Scalability**
- **Async/Await**: Non-blocking I/O with AsyncIO + SQLAlchemy async
- **Connection Pooling**: Efficient PostgreSQL and Redis connection management
- **SSE Streaming**: Progressive responses for better UX
- **Dual-Persistence**: Input persistence before streaming + real-time chunk aggregation

---

## 🚀 **Quick Start**

### **Option 1: Docker Compose (Recommended)**

```bash
# Clone the repository
git clone https://github.com/LuisHBarros/resilient-chat-platform.git
cd resilient-chat-platform

# Configure environment variables
cp .env.example .env
# Edit .env with your OpenAI credentials (or use mock)

# Start the entire stack
docker-compose up -d

# Access the API
curl http://localhost:8000/health
```

**Available services:**
- 🌐 API: http://localhost:8000
- 📚 Swagger UI: http://localhost:8000/docs
- 🔍 Jaeger UI: http://localhost:16686
- 📊 Prometheus: http://localhost:9090
- 📈 Grafana: http://localhost:3000

### **Option 2: Local Development**

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure .env
cp .env.example .env

# Run migrations
alembic upgrade head

# Run application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📚 **Complete Documentation**

- **[API Reference](/docs/API.md)** - Complete REST endpoints guide
- **[Architecture Decision Records (ADRs)](/docs/README.md)** - Documented architectural decisions
- **[System Design](/docs/)** - Diagrams and applied patterns

---

## 🏗️ **Layered Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                            │
│  (FastAPI routes, DTOs, Middleware, Error Handlers)         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                         │
│        (Use Cases: ProcessMessage, StreamMessage)           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     Domain Layer                            │
│   (Entities, Value Objects, Ports/Interfaces, Business)     │
│                       Rules)                                │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                       │
│  (LLM Adapters, PostgreSQL, Redis, Keycloak, Telemetry)    │
└─────────────────────────────────────────────────────────────┘
```

**Applied Principles:**
- ✅ Dependency Inversion (inner layers don't know outer layers)
- ✅ Separation of Concerns (each layer has a single responsibility)
- ✅ Testability (easy to create fakes/mocks because of Ports)
- ✅ Flexibility (switching PostgreSQL to MongoDB affects only 1 adapter)

---

## 🔌 **Main Endpoints**

### **Chat**
```bash
# Send message with streaming (SSE)
POST /api/v1/chat/message/stream
Content-Type: application/json
{
  "conversation_id": "uuid",
  "content": "Hello, how are you?",
  "user_id": "user123"
}

# Send message without streaming
POST /api/v1/chat/message
```

### **Health Checks**
```bash
# Basic health check
GET /health

# Readiness check (verifies dependencies)
GET /health/ready
```

See [complete API documentation](/docs/API.md).

---

## ⚙️ **Configuration**

### **Main Environment Variables**

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/chat_db

# LLM Provider
LLM_PROVIDER=openai  # or 'mock' for development
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4

# Resilience
LLM_FALLBACK_ENABLED=true
LLM_CIRCUIT_BREAKER_THRESHOLD=5
LLM_RETRY_MAX_ATTEMPTS=3

# Observability
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4318
PROMETHEUS_ENABLED=true

# Cache
REDIS_URL=redis://localhost:6379/0

# Security
KEYCLOAK_URL=http://localhost:8080
```

See `.env.example` for complete configuration.

---

## 🧪 **Testing**

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific tests
pytest tests/unit/test_process_message_use_case.py -v

# Contract tests (verify Ports)
pytest tests/contract/
```

**Current Coverage:** ~85% (focus on business logic and use cases)

**Test Types:**
- ✅ **Unit Tests**: Isolated use cases with fakes
- ✅ **Contract Tests**: Verify adapters correctly implement Ports
- ✅ **Integration Tests**: API endpoints (in development)

---

## 📦 **Project Structure**

```
resilient-chat-platform/
├── app/
│   ├── api/                    # API layer (routes, DTOs, middleware)
│   │   ├── routes/
│   │   ├── dto/
│   │   └── middleware/
│   ├── application/            # Use cases (business logic)
│   │   └── use_cases/
│   ├── domain/                 # Entities, Value Objects, Ports
│   │   ├── entities/
│   │   ├── value_objects/
│   │   └── ports/
│   ├── infrastructure/         # Adapters (LLM, DB, Logging, Telemetry)
│   │   ├── llm/
│   │   ├── database/
│   │   ├── logging/
│   │   └── telemetry/
│   ├── bootstrap.py            # Dependency Injection Container
│   └── main.py                 # FastAPI app entry point
├── alembic/                    # Database migrations
├── tests/                      # Test suites
│   ├── unit/
│   ├── contract/
│   └── integration/
├── docs/                       # Architecture documentation
├── infra/                      # Docker Compose, Kubernetes configs
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## 🛠️ **For Developers**

### **Adding a New LLM Provider**

1. Implement `LLMPort` in `app/infrastructure/llm/`
2. Register in factory (`app/infrastructure/llm/factory.py`)
3. Add configuration in `settings.py`
4. Create contract tests

```python
# Simplified example
class AnthropicAdapter(LLMPort):
    async def generate(self, prompt: str) -> str:
        # Anthropic-specific implementation
        ...
```

### **Adding a New Endpoint**

1. Create DTO in `app/api/dto/`
2. Create use case in `app/application/use_cases/`
3. Create route in `app/api/routes/`
4. Register in `app/main.py`

---

## 🔍 **Observability in Practice**

### **Distributed Trace Example**

```
[Request ID: abc123] POST /api/v1/chat/message/stream
  ├── [Span 1] validate_request          → 2ms
  ├── [Span 2] get_conversation_from_db  → 15ms
  ├── [Span 3] call_llm_provider         → 1850ms
  │   ├── [Sub-span] openai_api_call     → 1800ms
  │   └── [Sub-span] fallback_to_gpt4    → 50ms (Circuit Open!)
  └── [Span 4] persist_response          → 8ms
Total: 1875ms
```

This allows you to identify bottlenecks instantly in the Jaeger UI.

---

## 🌐 **Applicability to Logistics Systems**

This project demonstrates patterns directly applicable to delivery/tracking platforms:

| Implemented Pattern | Logistics Application |
|---------------------|------------------------|
| **Circuit Breaker** | Failover between carriers (USPS → Carrier A → B) |
| **Event Streaming** | Real-time delivery status tracking |
| **OpenTelemetry** | Journey tracking: order → separation → transport → delivery |
| **Hexagonal Arch** | Integration with multiple logistics partners without coupling |
| **Dual-Persistence** | Ensure tracking events are never lost |

---

## 🤝 **Contributing**

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

---

## 📄 **License**

[MIT](LICENSE)

---

## 👤 **Author**

**Luis H. Barros**
- GitHub: [@LuisHBarros](https://github.com/LuisHBarros)
- LinkedIn: [Luis Henrique de Barros](https://www.linkedin.com/in/luis-henrique-de-barros-207929226/)
- Email: luishrbr@gmail.com

---

## 🙏 **Acknowledgments**

- Clean Architecture concepts from Uncle Bob Martin
- Hexagonal Architecture (Alistair Cockburn)
- FastAPI community
- OpenTelemetry project

---

**💡 This project is part of my technical portfolio, demonstrating the ability to build robust, observable, and scalable backend systems following industry best practices.**
