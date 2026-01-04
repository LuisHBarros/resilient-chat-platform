# API Documentation

Documentação completa da API REST do Chat Service.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Base URL](#base-url)
- [Autenticação](#autenticação)
- [Endpoints](#endpoints)
- [Modelos de Dados](#modelos-de-dados)
- [Códigos de Status](#códigos-de-status)
- [Exemplos de Uso](#exemplos-de-uso)
- [Configuração](#configuração)
- [Observabilidade](#observabilidade)

## Visão Geral

A API do Chat Service fornece endpoints para:
- Enviar mensagens e receber respostas da IA
- Streaming de respostas em tempo real (SSE)
- Health checks e readiness probes
- Gerenciamento de conversas

A API segue os princípios REST e utiliza:
- **FastAPI** como framework
- **Pydantic** para validação de dados
- **Server-Sent Events (SSE)** para streaming
- **Correlation IDs** para rastreamento de requisições

## Base URL

```
http://localhost:8000/api/v1
```

Quando executado via Docker Compose, a API está disponível em:
- **Interno (Docker network)**: `http://chat-api:8000/api/v1`
- **Externo**: `http://localhost:8000/api/v1`
- **Via Traefik**: `http://localhost/api/v1` (quando configurado)

## Autenticação

⚠️ **Nota**: A autenticação ainda não está implementada nos endpoints. Os endpoints atualmente aceitam requisições sem autenticação.

## Endpoints

### 1. Enviar Mensagem (Streaming)

Envia uma mensagem e recebe a resposta da IA em tempo real via Server-Sent Events.

**Endpoint**: `POST /chat/message/stream`

**Headers**:
```
Content-Type: application/json
Accept: text/event-stream
```

**Request Body**:
```json
{
  "message": "Hello, how are you?",
  "user_id": "user-123",
  "conversation_id": "conv-456",
  "model_id": "gpt-4"
}
```

**Campos**:
- `message` (obrigatório): Conteúdo da mensagem (1-10000 caracteres)
- `user_id` (opcional): Identificador do usuário (padrão: "default_user")
- `conversation_id` (opcional): ID da conversa para continuar uma conversa existente
- `model_id` (opcional): ID do modelo para sobrescrever o padrão

**Response**: Server-Sent Events (SSE)

**Formato SSE**:
```
data: {"chunk": "Hello"}\n\n
data: {"chunk": ", "}\n\n
data: {"chunk": "I'm"}\n\n
data: {"chunk": " doing"}\n\n
data: {"chunk": " well"}\n\n
data: {"done": true}\n\n
```

**Eventos de Erro**:
```
data: {"error": "LLM service error", "type": "llm_error"}\n\n
data: {"error": "Database error", "type": "repository_error"}\n\n
data: {"error": "Unexpected error", "type": "unexpected_error"}\n\n
```

**Status Codes**:
- `200 OK`: Streaming iniciado com sucesso
- `400 Bad Request`: Dados inválidos
- `500 Internal Server Error`: Erro antes do streaming iniciar
- `503 Service Unavailable`: Serviço LLM indisponível

**Exemplo de Uso (JavaScript)**:
```javascript
const eventSource = new EventSource('http://localhost:8000/api/v1/chat/message/stream', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: 'Hello, how are you?',
    user_id: 'user-123'
  })
});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.chunk) {
    console.log('Chunk:', data.chunk);
  } else if (data.done) {
    console.log('Streaming completo');
    eventSource.close();
  } else if (data.error) {
    console.error('Erro:', data.error);
    eventSource.close();
  }
};
```

**Exemplo de Uso (cURL)**:
```bash
curl -N -X POST http://localhost:8000/api/v1/chat/message/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?",
    "user_id": "user-123"
  }'
```

### 2. Enviar Mensagem (Não-Streaming)

Envia uma mensagem e recebe a resposta completa da IA.

**Endpoint**: `POST /chat/message`

**Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "message": "Hello, how are you?",
  "user_id": "user-123",
  "conversation_id": "conv-456",
  "model_id": "gpt-4"
}
```

**Response**:
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "response": "I'm doing well, thank you! How can I help you today?",
  "user_message": "Hello, how are you?",
  "assistant_message": "I'm doing well, thank you! How can I help you today?"
}
```

**Status Codes**:
- `200 OK`: Mensagem processada com sucesso
- `400 Bad Request`: Dados inválidos ou erro de aplicação
- `500 Internal Server Error`: Erro no repositório
- `503 Service Unavailable`: Erro no serviço LLM

**Exemplo de Uso (cURL)**:
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?",
    "user_id": "user-123"
  }'
```

### 3. Health Check

Verifica se o serviço está rodando.

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "ok"
}
```

**Status Codes**:
- `200 OK`: Serviço está rodando

### 4. Readiness Check

Verifica se o serviço está pronto para receber requisições, testando conectividade com dependências.

**Endpoint**: `GET /health/ready`

**Response** (Sucesso):
```json
{
  "status": "ready",
  "checks": {
    "llm": {
      "status": "healthy",
      "response_received": true
    },
    "repository": {
      "status": "healthy"
    }
  }
}
```

**Response** (Falha):
```json
{
  "status": "not_ready",
  "checks": {
    "llm": {
      "status": "unhealthy",
      "error": "LLM provider timeout (no response within 5 seconds)"
    },
    "repository": {
      "status": "unhealthy",
      "error": "Database connection test failed"
    }
  }
}
```

**Status Codes**:
- `200 OK`: Todos os componentes estão saudáveis
- `503 Service Unavailable`: Um ou mais componentes estão indisponíveis

**Exemplo de Uso**:
```bash
curl http://localhost:8000/health/ready
```

## Modelos de Dados

### MessageRequestDTO

```typescript
{
  message: string;           // 1-10000 caracteres, obrigatório
  user_id?: string;          // 1-100 caracteres, opcional
  conversation_id?: string;  // 1-100 caracteres, opcional
  model_id?: string;         // 1-200 caracteres, opcional
}
```

**Validações**:
- `message`: Não pode ser vazio ou apenas espaços em branco
- Todos os campos opcionais têm limites de tamanho

### MessageResponseDTO

```typescript
{
  conversation_id: string;  // UUID da conversa
  response: string;         // Resposta completa da IA
  user_message: string;     // Mensagem original do usuário
  assistant_message: string; // Resposta da IA (igual a response)
}
```

## Códigos de Status

| Código | Significado | Quando Ocorre |
|--------|-------------|---------------|
| `200` | OK | Requisição bem-sucedida |
| `400` | Bad Request | Dados inválidos ou erro de aplicação |
| `500` | Internal Server Error | Erro no repositório ou erro inesperado |
| `503` | Service Unavailable | Serviço LLM indisponível ou erro de infraestrutura |

## Exemplos de Uso

### Exemplo 1: Nova Conversa com Streaming

```bash
curl -N -X POST http://localhost:8000/api/v1/chat/message/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explique o que é machine learning",
    "user_id": "user-123"
  }'
```

### Exemplo 2: Continuar Conversa Existente

```bash
curl -N -X POST http://localhost:8000/api/v1/chat/message/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "E deep learning?",
    "user_id": "user-123",
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

### Exemplo 3: Resposta Completa (Sem Streaming)

```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Qual é a capital do Brasil?",
    "user_id": "user-123"
  }'
```

### Exemplo 4: Usando Python

```python
import requests
import json

# Streaming
response = requests.post(
    'http://localhost:8000/api/v1/chat/message/stream',
    json={
        'message': 'Hello, how are you?',
        'user_id': 'user-123'
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        data = json.loads(line.decode('utf-8').replace('data: ', ''))
        if 'chunk' in data:
            print(data['chunk'], end='', flush=True)
        elif 'done' in data:
            print('\nStreaming completo')
            break
        elif 'error' in data:
            print(f'\nErro: {data["error"]}')
            break

# Não-streaming
response = requests.post(
    'http://localhost:8000/api/v1/chat/message',
    json={
        'message': 'Hello, how are you?',
        'user_id': 'user-123'
    }
)
print(response.json())
```

## Configuração

### Variáveis de Ambiente

A API utiliza as seguintes variáveis de ambiente (configuradas no `docker-compose.yml`):

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `DATABASE_URL` | URL de conexão do PostgreSQL | `postgresql+asyncpg://user:pass@db:5432/chat_db` |
| `REDIS_URL` | URL de conexão do Redis | `redis://redis:6379/0` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Endpoint do Jaeger para tracing | `http://jaeger:4317` |
| `LLM_PROVIDER` | Provedor LLM (`mock` ou `openai`) | `mock` |
| `OPENAI_API_KEY` | Chave da API OpenAI | - |
| `OPENAI_MODEL` | Modelo OpenAI a usar | `gpt-3.5-turbo` |
| `LLM_FALLBACK_ENABLED` | Habilitar fallback automático | `true` |
| `LLM_STREAMING_TIMEOUT` | Timeout para streaming (segundos) | `30.0` |
| `API_PREFIX` | Prefixo da API | `/api/v1` |
| `DEBUG` | Modo debug | `false` |

### Configuração via Docker Compose

As variáveis são configuradas no `docker-compose.yml`:

```yaml
chat-api:
  environment:
    - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/chat_db
    - REDIS_URL=redis://redis:6379/0
    - OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
    - LLM_PROVIDER=${LLM_PROVIDER:-mock}
    - OPENAI_API_KEY=${OPENAI_API_KEY:-}
```

## Observabilidade

### Correlation IDs

Todas as requisições recebem um Correlation ID único no header `X-Correlation-ID`. Este ID é usado para rastrear requisições através dos logs e traces.

**Header**:
```
X-Correlation-ID: 550e8400-e29b-41d4-a716-446655440000
```

### Logs

A API utiliza structured logging com os seguintes campos:
- `correlation_id`: ID único da requisição
- `timestamp`: Timestamp ISO 8601
- `level`: Nível do log (INFO, ERROR, etc.)
- `message`: Mensagem do log
- `context`: Contexto adicional (user_id, conversation_id, etc.)

### Métricas

Métricas são coletadas pelo Prometheus (quando o endpoint `/metrics` for implementado):
- Número de requisições por endpoint
- Tempo de resposta
- Taxa de erro
- Uso de recursos

**Acesso**: http://localhost:9090

### Tracing

Traces distribuídos são enviados para o Jaeger:
- Rastreamento de requisições através de múltiplos serviços
- Visualização de latência e dependências

**Acesso**: http://localhost:16686

### Dashboards

Dashboards do Grafana para visualização de métricas:
- Performance da API
- Uso de recursos
- Taxa de erro

**Acesso**: http://localhost:3000 (admin/admin)

## Documentação Interativa (Swagger/OpenAPI)

A API expõe documentação interativa via Swagger UI:

**URL**: http://localhost:8000/docs

**ReDoc**: http://localhost:8000/redoc

**OpenAPI JSON**: http://localhost:8000/openapi.json

## Limitações e Considerações

1. **Rate Limiting**: Não implementado ainda (será via Redis)
2. **Autenticação**: Não implementada
3. **Validação de Modelo**: O campo `model_id` é aceito, mas ainda não é utilizado
4. **Tamanho de Mensagem**: Limitado a 10.000 caracteres
5. **Timeout de Streaming**: 30 segundos (configurável via `LLM_STREAMING_TIMEOUT`)

## Suporte e Contribuição

Para questões, bugs ou sugestões, consulte:
- [Documentação do Projeto](../README.md)
- [ADRs (Architecture Decision Records)](./adr/README.md)
- [Diagramas de Arquitetura](./diagrams/README.md)

