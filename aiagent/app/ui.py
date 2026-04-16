import streamlit as st
import requests
import json
import uuid
import time

st.set_page_config(page_title="AI RAG Agent", page_icon="🤖", layout="wide")

API = st.sidebar.text_input("API URL", "http://localhost:8000")

# ── Init session state ─────────────────────────────────────────────────────────
for k, v in {"token": None, "username": "", "chat_history": [], "session_id": str(uuid.uuid4())}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar: Login ─────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.subheader("🔑 Login")
username = st.sidebar.text_input("Username", value="admin")
password = st.sidebar.text_input("Password", type="password", value="admin")

if st.sidebar.button("Login"):
    r = requests.post(f"{API}/auth/token", data={"username": username, "password": password})
    if r.status_code == 200:
        st.session_state.token = r.json()["access_token"]
        st.session_state.username = username
        st.sidebar.success(f"✅ Loggato come {username}")
    else:
        st.sidebar.error("❌ Credenziali errate")

headers = {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}
logged_in = st.session_state.token is not None
st.sidebar.markdown("🟢 **Autenticato**" if logged_in else "🔴 **Non autenticato**")

# ── Sidebar: sessioni passate ──────────────────────────────────────────────────
if logged_in:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📂 Sessioni passate")
    try:
        sess_r = requests.get(f"{API}/sessions", headers=headers, timeout=5)
        if sess_r.status_code == 200:
            sessions = sess_r.json()
            for s in sessions[:10]:
                label = f"{s['session_id'][:8]}… ({s['msg_count']} msg)"
                if st.sidebar.button(label, key=s["session_id"]):
                    hist_r = requests.get(f"{API}/history/{s['session_id']}", headers=headers, timeout=5)
                    if hist_r.status_code == 200:
                        st.session_state.session_id = s["session_id"]
                        st.session_state.chat_history = [
                            {"role": m["role"], "content": m["content"],
                             "sources": m.get("sources", []), "confidence": m.get("confidence", 0)}
                            for m in hist_r.json()
                        ]
                        st.rerun()
    except Exception:
        pass

    if st.sidebar.button("➕ Nuova sessione"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.chat_history = []
        st.rerun()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_chat, tab_ingest, tab_info = st.tabs(["💬 Chat", "📄 Documenti", "ℹ️ Info"])

# ── TAB CHAT ───────────────────────────────────────────────────────────────────
with tab_chat:
    st.markdown(f"## Chat  `{st.session_state.session_id[:8]}…`")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("sources"):
                with st.expander(f"📎 {len(msg['sources'])} fonti · confidence {msg.get('confidence', 0):.0%}"):
                    for s in msg["sources"]:
                        score = s.get("rerank_score")
                        loc = f"pag. {s['page']}" if s.get("page") else f"chunk {s.get('chunk')}"
                        sc = f" · score {score:.3f}" if score is not None else ""
                        st.markdown(f"- **{s['source']}** — {loc}{sc}")

    if prompt := st.chat_input("Fai una domanda..."):
        if not logged_in:
            st.warning("⚠️ Devi prima effettuare il login.")
        else:
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                placeholder = st.empty()
                full_text = ""
                sources, confidence = [], 0.0

                # True SSE streaming
                try:
                    with requests.post(
                        f"{API}/chat/stream",
                        headers=headers,
                        json={"question": prompt, "session_id": st.session_state.session_id},
                        stream=True, timeout=90,
                    ) as resp:
                        if resp.status_code == 200:
                            for line in resp.iter_lines(decode_unicode=True):
                                if line.startswith("data:"):
                                    raw = line[5:].strip()
                                    try:
                                        data = json.loads(raw)
                                        if "token" in data:
                                            full_text += data["token"]
                                            placeholder.markdown(full_text + "▌")
                                        if data.get("done"):
                                            sources = data.get("sources", [])
                                    except Exception:
                                        pass
                            placeholder.markdown(full_text)
                        elif resp.status_code == 429:
                            full_text = f"⏳ Rate limit raggiunto. {resp.json().get('detail', '')}"
                            placeholder.markdown(full_text)
                        else:
                            full_text = f"❌ Errore {resp.status_code}"
                            placeholder.markdown(full_text)
                except Exception as e:
                    full_text = f"❌ {e}"
                    placeholder.markdown(full_text)

            st.session_state.chat_history.append({
                "role": "assistant", "content": full_text,
                "sources": sources, "confidence": confidence,
            })
            st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑️ Pulisci chat"):
            st.session_state.chat_history = []
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()

# ── TAB INGEST ─────────────────────────────────────────────────────────────────
with tab_ingest:
    st.markdown("## Carica documenti")
    st.info("Richiede ruolo **admin**. Formati: PDF, TXT, MD.")
    uploaded = st.file_uploader("Seleziona file", type=["pdf", "txt", "md"], accept_multiple_files=True)
    if st.button("📤 Carica") and uploaded:
        if not logged_in:
            st.warning("⚠️ Login richiesto.")
        else:
            file_tuples = [("files", (f.name, f.read(), f.type)) for f in uploaded]
            with st.spinner("Ingesting..."):
                try:
                    r = requests.post(f"{API}/ingest", headers=headers, files=file_tuples, timeout=120)
                    if r.status_code == 200:
                        d = r.json()
                        st.success(f"✅ {d['ingested']} chunks da: {', '.join(d['files'])}")
                    elif r.status_code == 403:
                        st.error("❌ Accesso negato: serve ruolo admin.")
                    else:
                        st.error(f"❌ Errore {r.status_code}: {r.text}")
                except Exception as e:
                    st.error(f"❌ {e}")

# ── TAB INFO ───────────────────────────────────────────────────────────────────
with tab_info:
    st.markdown("## Stato sistema")
    try:
        r = requests.get(f"{API}/health", timeout=5)
        d = r.json()
        if r.status_code == 200:
            st.success(f"✅ API online — v{d.get('version', '?')}")
        else:
            st.error("❌ API non risponde")
    except Exception:
        st.error("❌ Impossibile raggiungere l'API")

    st.markdown("""
| Componente | Dettaglio |
|---|---|
| **LLM** | GPT-4o-mini, true token streaming (SSE) |
| **Embeddings** | text-embedding-3-small |
| **Vector Store** | ChromaDB |
| **Retrieval** | k=12 → CrossEncoder reranker top-4 |
| **Orchestration** | LangGraph StateGraph |
| **Auth** | JWT HS256 (python-jose + bcrypt) |
| **Rate limit** | Sliding window, configurabile |
| **Chat History** | SQLite (sostituibile con Postgres) |
| **Tracing** | Langfuse self-hosted |
| **API** | FastAPI 0.5.0 + Uvicorn |
| **UI** | Streamlit |
    """)
    st.markdown("### Session ID corrente")
    st.code(st.session_state.session_id)
