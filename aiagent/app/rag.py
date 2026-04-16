import os, io
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from app.reranker import rerank

load_dotenv()
CHROMA_DIR = os.getenv("CHROMA_DIR", "./data/chroma")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
RETRIEVAL_K = int(os.getenv("RETRIEVAL_K", "12"))   # recupera largo
RERANKER_TOP_N = int(os.getenv("RERANKER_TOP_N", "4"))  # poi stringe

embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
vs = Chroma(collection_name="docs", embedding_function=embeddings, persist_directory=CHROMA_DIR)
splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)


def _load_docs(name: str, data: bytes):
    ext = name.lower().split(".")[-1]
    if ext == "pdf":
        reader = PdfReader(io.BytesIO(data))
        docs = []
        for i, page in enumerate(reader.pages):
            txt = page.extract_text() or ""
            if txt.strip():
                docs.append(Document(page_content=txt, metadata={"source": name, "page": i + 1}))
        return docs
    return [Document(page_content=data.decode("utf-8", errors="ignore"), metadata={"source": name})]


def ingest_files(files):
    total, names = 0, []
    for name, data in files:
        docs = _load_docs(name, data)
        chunks = splitter.split_documents(docs)
        for idx, ch in enumerate(chunks):
            ch.metadata.update({"chunk": idx + 1})
        vs.add_documents(chunks)
        total += len(chunks)
        names.append(name)
    return {"ingested": total, "files": names}


def retrieve_chunks(question: str, k: int = RETRIEVAL_K) -> list:
    """Retrieve broad, then rerank to top_n."""
    docs = vs.similarity_search(question, k=k)
    raw = [
        {
            "text": d.page_content,
            "source": d.metadata.get("source"),
            "chunk": d.metadata.get("chunk"),
            "page": d.metadata.get("page"),
        }
        for d in docs
    ]
    return rerank(question, raw, top_n=RERANKER_TOP_N)


def generate_answer(question: str, chunks: list):
    context = "

".join(
        f"[{c['source']}#{c.get('page') or c.get('chunk')}] (score:{c.get('rerank_score', '?')}) {c['text']}"
        for c in chunks
    )
    sources = [
        {"source": c["source"], "chunk": c.get("chunk"), "page": c.get("page"), "rerank_score": c.get("rerank_score")}
        for c in chunks
    ]
    llm = ChatOpenAI(model=CHAT_MODEL, temperature=0).with_structured_output({
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1}
        },
        "required": ["answer", "confidence"]
    })
    out = llm.invoke(
        f"Sei un agente RAG. Rispondi solo col contesto. Cita le fonti inline come [source#page].

"
        f"Contesto:
{context}

Domanda: {question}"
    )
    return out["answer"], sources, float(out.get("confidence", 0.7))
