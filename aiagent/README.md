# AI RAG Agent — v0.5.0

Agente RAG production-ready con LangGraph, reranker, JWT auth, rate limiting,
true SSE streaming, chat history persistente e Langfuse tracing.

## Requisiti
- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/) (package manager)

## Installa uv
```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# oppure via pip
pip install uv
```

## Avvio rapido
```bash
cp .env.example .env      # inserisci OPENAI_API_KEY

# 1. Crea venv e installa tutto
uv sync

# 2. API
uv run uvicorn app.main:app --reload

# 3. UI (in altro terminale)
uv run streamlit run app/ui.py

# Docker completo (API + UI + Langfuse + Postgres)
docker-compose up --build
```

## Gestione dipendenze con uv
```bash
# aggiungere una dipendenza
uv add httpx

# aggiungere una dev-dependency
uv add --dev pytest-cov

# rimuovere
uv remove cohere

# aggiornare tutto
uv lock --upgrade

# eseguire un comando nel venv senza attivarlo
uv run python -c "import fastapi; print(fastapi.__version__)"
```

## Stack completo
| Layer | Tecnologia |
|---|---|
| LLM | OpenAI GPT-4o-mini |
| Embeddings | text-embedding-3-small |
| Vector Store | ChromaDB |
| Retrieval | similarity_search k=12 → CrossEncoder reranker top-4 |
| Orchestration | LangGraph StateGraph + RetryPolicy |
| Streaming | OpenAI AsyncOpenAI + SSE |
| Auth | JWT HS256 (python-jose + passlib/bcrypt) |
| Rate Limiting | Sliding window in-memory |
| Chat History | SQLite (sostituibile con Postgres) |
| Tracing | Langfuse self-hosted |
| API | FastAPI 0.5.0 + Uvicorn |
| UI | Streamlit |
| Package manager | uv |

## Struttura
```
app/
├── auth.py        ← JWT auth, ruoli admin/reader
├── graph.py       ← LangGraph StateGraph
├── history.py     ← SQLite chat history
├── main.py        ← FastAPI endpoints
├── middleware.py  ← logging JSON strutturato
├── rag.py         ← ingest, retrieve, generate
├── ratelimit.py   ← sliding window rate limiter
├── reranker.py    ← CrossEncoder / Cohere / none
├── schemas.py     ← Pydantic models
├── streaming.py   ← true SSE token streaming
├── tracing.py     ← Langfuse callback
└── ui.py          ← Streamlit UI completa
```

## Endpoints
| Method | Path | Auth | Ruolo |
|---|---|---|---|
| POST | /auth/token | no | — |
| GET | /health | no | — |
| POST | /ingest | JWT | admin |
| POST | /chat | JWT | any |
| POST | /chat/stream | JWT | any |
| GET | /history/{session_id} | JWT | any |
| GET | /sessions | JWT | any |

## Auth curl
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/token \
  -d "username=admin&password=admin" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "cosa dice il documento?"}'
```

## JWT secret sicuro
```bash
uv run python -c "import secrets; print(secrets.token_hex(32))"
```
