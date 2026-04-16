import uuid
from typing import Annotated
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Depends, Query
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from app.rag import ingest_files, retrieve_chunks
from app.graph import rag_graph
from app.schemas import ChatResponse
from app.auth import get_current_user, require_admin, issue_token, TokenResponse, UserPayload
from app.middleware import RequestLoggingMiddleware
from app.tracing import get_langfuse_callback
from app.ratelimit import check_rate_limit
from app.history import init_db, save_message, get_history, list_sessions
from app.streaming import stream_tokens


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="AI RAG Agent", version="0.5.0", lifespan=lifespan)
app.add_middleware(RequestLoggingMiddleware)


class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None


# ── Auth ──────────────────────────────────────────────────────────────────────
@app.post("/auth/token", response_model=TokenResponse, tags=["auth"])
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()]):
    return issue_token(form)


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["system"])
def health():
    return {"ok": True, "version": "0.5.0"}


# ── Ingest ────────────────────────────────────────────────────────────────────
@app.post("/ingest", tags=["documents"])
async def ingest(
    files: list[UploadFile] = File(...),
    user: UserPayload = Depends(require_admin),
):
    payloads = [(f.filename, await f.read()) for f in files]
    return ingest_files(payloads)


# ── Chat (JSON) ───────────────────────────────────────────────────────────────
@app.post("/chat", response_model=ChatResponse, tags=["chat"])
def chat(req: ChatRequest, user: UserPayload = Depends(get_current_user)):
    check_rate_limit(user.username)
    session_id = req.session_id or str(uuid.uuid4())
    callbacks = get_langfuse_callback(user_id=user.username, session_id=session_id)

    save_message(session_id, user.username, "user", req.question)

    state = rag_graph.invoke(
        {"question": req.question, "chunks": [], "answer": "", "sources": [], "confidence": 0.0, "attempts": 0},
        config={"callbacks": callbacks},
    )
    answer = state.get("answer", "")
    sources = state.get("sources", [])
    confidence = state.get("confidence", 0.0)

    save_message(session_id, user.username, "assistant", answer, sources=sources, confidence=confidence)
    return {"answer": answer, "sources": sources, "confidence": confidence}


# ── Chat stream (SSE, true token streaming) ───────────────────────────────────
@app.post("/chat/stream", tags=["chat"])
async def chat_stream(req: ChatRequest, user: UserPayload = Depends(get_current_user)):
    check_rate_limit(user.username)
    session_id = req.session_id or str(uuid.uuid4())

    save_message(session_id, user.username, "user", req.question)
    chunks = retrieve_chunks(req.question)

    async def event_generator():
        full_text = ""
        sources = []
        async for event in stream_tokens(req.question, chunks):
            import json as _json
            yield event
            # accumula testo e sources per salvare in history
            try:
                data = _json.loads(event.removeprefix("data: ").strip())
                if "token" in data:
                    full_text += data["token"]
                if data.get("done"):
                    sources = data.get("sources", [])
            except Exception:
                pass
        save_message(session_id, user.username, "assistant", full_text, sources=sources)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ── History ───────────────────────────────────────────────────────────────────
@app.get("/history/{session_id}", tags=["chat"])
def get_session_history(
    session_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    user: UserPayload = Depends(get_current_user),
):
    return get_history(session_id, limit=limit)


@app.get("/sessions", tags=["chat"])
def get_sessions(
    limit: int = Query(default=50, ge=1, le=200),
    user: UserPayload = Depends(get_current_user),
):
    return list_sessions(user.username, limit=limit)
