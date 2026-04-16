"""
Reranker module — supporta 3 backend intercambiabili:
  1. HuggingFace cross-encoder locale (default, gratuito)
  2. Cohere Rerank API (cloud, più accurato)
  3. Fallback no-op (se sentence-transformers non installato)

Selezionato tramite variabile d'ambiente RERANKER_BACKEND=hf|cohere|none
"""
import os
from typing import List

RERANKER_BACKEND = os.getenv("RERANKER_BACKEND", "hf")
RERANKER_TOP_N = int(os.getenv("RERANKER_TOP_N", "4"))
HF_RERANKER_MODEL = os.getenv("HF_RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")
COHERE_RERANKER_MODEL = os.getenv("COHERE_RERANKER_MODEL", "rerank-v4.0-pro")


def rerank(query: str, chunks: List[dict], top_n: int = RERANKER_TOP_N) -> List[dict]:
    """Reordina i chunk per rilevanza rispetto alla query.
    Aggiunge 'rerank_score' a ogni chunk e ritorna top_n ordinati.
    """
    if not chunks:
        return chunks

    backend = RERANKER_BACKEND.lower()

    if backend == "cohere":
        return _cohere_rerank(query, chunks, top_n)
    elif backend == "hf":
        return _hf_rerank(query, chunks, top_n)
    else:
        return chunks[:top_n]


def _hf_rerank(query: str, chunks: List[dict], top_n: int) -> List[dict]:
    """Cross-encoder locale via sentence-transformers."""
    try:
        from sentence_transformers import CrossEncoder
    except ImportError:
        return chunks[:top_n]

    model = CrossEncoder(HF_RERANKER_MODEL)
    pairs = [[query, c["text"]] for c in chunks]
    scores = model.predict(pairs)
    ranked = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
    result = []
    for score, chunk in ranked[:top_n]:
        result.append({**chunk, "rerank_score": round(float(score), 4)})
    return result


def _cohere_rerank(query: str, chunks: List[dict], top_n: int) -> List[dict]:
    """Cohere Rerank v4 API."""
    try:
        import cohere
        co = cohere.Client(COHERE_API_KEY)
        texts = [c["text"] for c in chunks]
        response = co.rerank(
            model=COHERE_RERANKER_MODEL,
            query=query,
            documents=texts,
            top_n=top_n
        )
        result = []
        for r in response.results:
            chunk = {**chunks[r.index], "rerank_score": round(float(r.relevance_score), 4)}
            result.append(chunk)
        return result
    except Exception as e:
        return chunks[:top_n]
