"""
Langfuse tracing — drop-in callback per LangChain/LangGraph.
Supporta Langfuse v3 (self-hosted o cloud).

Uso:
    from app.tracing import get_langfuse_callback
    callbacks = get_langfuse_callback(user_id="...", session_id="...")
    rag_graph.invoke(state, config={"callbacks": callbacks})
"""
import os
from dotenv import load_dotenv

load_dotenv()
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")


def get_langfuse_callback(user_id: str = "anon", session_id: str | None = None):
    """Ritorna lista di callbacks da passare a LangChain/LangGraph.
    Se le credenziali non sono configurate, ritorna lista vuota silenziosamente.
    """
    if not LANGFUSE_SECRET_KEY or not LANGFUSE_PUBLIC_KEY:
        return []
    try:
        from langfuse.callback import CallbackHandler
        return [CallbackHandler(
            secret_key=LANGFUSE_SECRET_KEY,
            public_key=LANGFUSE_PUBLIC_KEY,
            host=LANGFUSE_HOST,
            user_id=user_id,
            session_id=session_id,
            trace_name="rag_agent",
        )]
    except ImportError:
        return []
