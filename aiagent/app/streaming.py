"""
True token-level streaming dal modello OpenAI.
Usa openai.AsyncOpenAI con stream=True e SSE (Server-Sent Events).
"""
import os, json
from typing import AsyncGenerator
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")


async def stream_tokens(question: str, chunks: list) -> AsyncGenerator[str, None]:
    """Yields SSE-formatted token chunks from the LLM."""
    context = "

".join(
        f"[{c['source']}#{c.get('page') or c.get('chunk')}] {c['text']}"
        for c in chunks
    )
    sources = [
        {"source": c["source"], "chunk": c.get("chunk"), "page": c.get("page"), "rerank_score": c.get("rerank_score")}
        for c in chunks
    ]
    prompt = (
        "Sei un agente RAG. Rispondi solo col contesto. Cita le fonti inline come [source#page].

"
        f"Contesto:
{context}

Domanda: {question}"
    )
    stream = await client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        temperature=0,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if delta:
            # SSE format: "data: <token>\n\n"
            yield f"data: {json.dumps({'token': delta})}

"

    # segnala fine stream + sources
    yield f"data: {json.dumps({'done': True, 'sources': sources})}

"
