# Backend IA Project - Chat Service

AI chat service built with FastAPI, following Clean Architecture and supporting multiple LLM providers.

## 🚀 Quick Start

### With Docker Compose (Recommended)

```bash
# From project root
docker-compose up -d chat-api
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your settings

# Run application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: http://localhost:8000

## 📚 Documentation

- **[API Documentation](./docs/API.md)** - Complete REST API guide
- **[Technical Documentation](./docs/README.md)** - ADRs, diagrams, and architecture
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🏗️ Architecture

The project follows **Clean Architecture** with the following layers:

- **Domain**: Entities, Value Objects, and Ports (interfaces)
- **Application**: Use cases
- **Infrastructure**: Concrete implementations (LLM, DB, Logging)
- **API**: REST endpoints and DTOs

### Main Components

- **FastAPI**: Web framework
- **SQLAlchemy (async)**: ORM for PostgreSQL
- **Pydantic**: Data validation
- **Alembic**: Database migrations
- **pgvector**: PostgreSQL extension for vector search (RAG)

## 🔌 Main Endpoints

### Chat

- `POST /api/v1/chat/message/stream` - Send message with SSE streaming
- `POST /api/v1/chat/message` - Send message without streaming

### Health

- `GET /health` - Basic health check
- `GET /health/ready` - Readiness check (verifies dependencies)

See the [complete API documentation](./docs/API.md) for details.

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL URL | - |
| `REDIS_URL` | Redis URL | - |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Jaeger endpoint | - |
| `LLM_PROVIDER` | LLM provider (`mock` or `openai`) | `mock` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `OPENAI_MODEL` | OpenAI model | `gpt-3.5-turbo` |
| `LLM_FALLBACK_ENABLED` | Enable fallback | `true` |
| `API_PREFIX` | API prefix | `/api/v1` |
| `DEBUG` | Debug mode | `false` |

### Example `.env`

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/chat_db
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
```

## 🗄️ Database

### Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "change description"

# Apply migrations
alembic upgrade head

# Revert migration
alembic downgrade -1
```

### pgvector Extension

The `chat_db` database uses the `pgvector` extension for vector search (RAG). The extension is automatically enabled via initialization script.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific tests
pytest tests/unit/test_process_message_use_case.py
```

### Test Types

- **Unit Tests**: Test use cases in isolation with fakes
- **Contract Tests**: Test interface contracts (ports)
- **Integration Tests**: Test API endpoints

## 📦 Project Structure

```
backend-ia-proj/
├── app/
│   ├── api/              # API layer (endpoints, DTOs, middleware)
│   ├── application/      # Use cases
│   ├── domain/           # Entities, Value Objects, Ports
│   ├── infrastructure/   # Implementations (LLM, DB, Logging)
│   ├── bootstrap.py      # Dependency container
│   └── main.py           # Entry point
├── alembic/              # Database migrations
├── tests/                # Tests
├── docs/                 # Documentation
└── Dockerfile            # Docker image
```

## 🔍 Observability

### Logs

The application uses structured logging with correlation IDs for request tracking.

### Metrics

Metrics are collected by Prometheus (when implemented):
- Request count
- Response time
- Error rate

### Tracing

Distributed traces are sent to Jaeger for latency and dependency visualization.

## 🛠️ Development

### Adding a New LLM Provider

1. Implement `LLMPort` in `app/infrastructure/llm/`
2. Register in factory (`app/infrastructure/llm/factory.py`)
3. Add configuration in `settings.py`
4. Create contract tests

### Adding a New Endpoint

1. Create DTO in `app/api/dto/`
2. Create use case in `app/application/use_cases/`
3. Create route in `app/api/routes/`
4. Register route in `app/main.py`

## 📝 License

[Add your license here]

## 🤝 Contributing

[Add contribution instructions here]
