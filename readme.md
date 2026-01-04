# Backend IA Project - Chat Service

Serviço de chat com IA construído com FastAPI, seguindo Clean Architecture e suportando múltiplos provedores de LLM.

## 🚀 Início Rápido

### Com Docker Compose (Recomendado)

```bash
# Na raiz do projeto
docker-compose up -d chat-api
```

### Desenvolvimento Local

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações

# Executar aplicação
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

A API estará disponível em: http://localhost:8000

## 📚 Documentação

- **[Documentação da API](./docs/API.md)** - Guia completo da API REST
- **[Documentação Técnica](./docs/README.md)** - ADRs, diagramas e arquitetura
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🏗️ Arquitetura

O projeto segue **Clean Architecture** com as seguintes camadas:

- **Domain**: Entidades, Value Objects e Ports (interfaces)
- **Application**: Casos de uso (use cases)
- **Infrastructure**: Implementações concretas (LLM, DB, Logging)
- **API**: Endpoints REST e DTOs

### Principais Componentes

- **FastAPI**: Framework web
- **SQLAlchemy (async)**: ORM para PostgreSQL
- **Pydantic**: Validação de dados
- **Alembic**: Migrações de banco de dados
- **pgvector**: Extensão PostgreSQL para busca vetorial (RAG)

## 🔌 Endpoints Principais

### Chat

- `POST /api/v1/chat/message/stream` - Enviar mensagem com streaming SSE
- `POST /api/v1/chat/message` - Enviar mensagem sem streaming

### Health

- `GET /health` - Health check básico
- `GET /health/ready` - Readiness check (verifica dependências)

Consulte a [documentação completa da API](./docs/API.md) para detalhes.

## ⚙️ Configuração

### Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `DATABASE_URL` | URL do PostgreSQL | - |
| `REDIS_URL` | URL do Redis | - |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Endpoint do Jaeger | - |
| `LLM_PROVIDER` | Provedor LLM (`mock` ou `openai`) | `mock` |
| `OPENAI_API_KEY` | Chave da API OpenAI | - |
| `OPENAI_MODEL` | Modelo OpenAI | `gpt-3.5-turbo` |
| `LLM_FALLBACK_ENABLED` | Habilitar fallback | `true` |
| `API_PREFIX` | Prefixo da API | `/api/v1` |
| `DEBUG` | Modo debug | `false` |

### Exemplo de `.env`

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/chat_db
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
```

## 🗄️ Banco de Dados

### Migrações

```bash
# Criar nova migração
alembic revision --autogenerate -m "descrição da mudança"

# Aplicar migrações
alembic upgrade head

# Reverter migração
alembic downgrade -1
```

### Extensão pgvector

O banco `chat_db` utiliza a extensão `pgvector` para busca vetorial (RAG). A extensão é ativada automaticamente via script de inicialização.

## 🧪 Testes

```bash
# Executar todos os testes
pytest

# Executar com cobertura
pytest --cov=app --cov-report=html

# Executar testes específicos
pytest tests/unit/test_process_message_use_case.py
```

### Tipos de Testes

- **Unit Tests**: Testam casos de uso isoladamente com fakes
- **Contract Tests**: Testam contratos de interfaces (ports)
- **Integration Tests**: Testam endpoints da API

## 📦 Estrutura do Projeto

```
backend-ia-proj/
├── app/
│   ├── api/              # Camada de API (endpoints, DTOs, middleware)
│   ├── application/      # Casos de uso (use cases)
│   ├── domain/           # Entidades, Value Objects, Ports
│   ├── infrastructure/   # Implementações (LLM, DB, Logging)
│   ├── bootstrap.py      # Container de dependências
│   └── main.py           # Entry point
├── alembic/              # Migrações de banco de dados
├── tests/                # Testes
├── docs/                 # Documentação
└── Dockerfile            # Imagem Docker
```

## 🔍 Observabilidade

### Logs

A aplicação utiliza structured logging com correlation IDs para rastreamento de requisições.

### Métricas

Métricas são coletadas pelo Prometheus (quando implementado):
- Número de requisições
- Tempo de resposta
- Taxa de erro

### Tracing

Traces distribuídos são enviados para o Jaeger para visualização de latência e dependências.

## 🛠️ Desenvolvimento

### Adicionar Novo Provedor LLM

1. Implementar `LLMPort` em `app/infrastructure/llm/`
2. Registrar no factory (`app/infrastructure/llm/factory.py`)
3. Adicionar configuração em `settings.py`
4. Criar testes de contrato

### Adicionar Novo Endpoint

1. Criar DTO em `app/api/dto/`
2. Criar caso de uso em `app/application/use_cases/`
3. Criar rota em `app/api/routes/`
4. Registrar rota em `app/main.py`

## 📝 Licença

[Adicione sua licença aqui]

## 🤝 Contribuindo

[Adicione instruções de contribuição aqui]
