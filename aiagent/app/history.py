"""
Persistent chat history su SQLite (zero-deps extra).
Sostituibile con PostgreSQL cambiando solo la connection string.

Tabella: messages(id, session_id, user_id, role, content, sources_json, confidence, ts)
"""
import sqlite3, json, os, time
from pathlib import Path
from dataclasses import dataclass

DB_PATH = os.getenv("HISTORY_DB", "./data/history.db")


def _conn():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with _conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT NOT NULL,
                user_id     TEXT NOT NULL,
                role        TEXT NOT NULL,
                content     TEXT NOT NULL,
                sources     TEXT DEFAULT '[]',
                confidence  REAL DEFAULT 0,
                ts          REAL NOT NULL
            )
        """)
        con.execute("CREATE INDEX IF NOT EXISTS idx_session ON messages(session_id)")


def save_message(session_id: str, user_id: str, role: str, content: str,
                 sources: list | None = None, confidence: float = 0.0):
    with _conn() as con:
        con.execute(
            "INSERT INTO messages(session_id, user_id, role, content, sources, confidence, ts) VALUES (?,?,?,?,?,?,?)",
            (session_id, user_id, role, content, json.dumps(sources or []), confidence, time.time())
        )


def get_history(session_id: str, limit: int = 20) -> list[dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT role, content, sources, confidence, ts FROM messages WHERE session_id=? ORDER BY ts DESC LIMIT ?",
            (session_id, limit)
        ).fetchall()
    return [
        {
            "role": r["role"],
            "content": r["content"],
            "sources": json.loads(r["sources"]),
            "confidence": r["confidence"],
            "ts": r["ts"],
        }
        for r in reversed(rows)
    ]


def list_sessions(user_id: str, limit: int = 50) -> list[dict]:
    with _conn() as con:
        rows = con.execute("""
            SELECT session_id, MAX(ts) as last_ts, COUNT(*) as msg_count
            FROM messages WHERE user_id=?
            GROUP BY session_id ORDER BY last_ts DESC LIMIT ?
        """, (user_id, limit)).fetchall()
    return [{"session_id": r["session_id"], "last_ts": r["last_ts"], "msg_count": r["msg_count"]} for r in rows]
