#!/usr/bin/env python3
"""
Session Pilot Pro Plus — SQLite Storage Adapter
================================================
Better concurrency, faster queries, single file.
Stdlib only (sqlite3), Python 3.8+.
"""

import sqlite3
import json
import os
import re
import time
import hashlib
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

# ─── Config ──────────────────────────────────────────────────────────────
DEFAULT_HOME = Path.home() / ".session-pilot-pro-plus"
HOME = Path(os.environ.get("SESSION_PILOT_HOME", DEFAULT_HOME))
HOME.mkdir(parents=True, exist_ok=True)
DB_PATH = HOME / "storage.db"


# ─── Security & Sanitization ─────────────────────────────────────────────
SECRET_PATTERNS = [
    (re.compile(r'ey[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'), '[REDACTED_JWT]'),
    (re.compile(r'AKIA[0-9A-Z]{16}'), '[REDACTED_AWS_KEY]'),
    (re.compile(r'(ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{30,})'), '[REDACTED_GITHUB_TOKEN]'),
    (re.compile(r'sk-[a-zA-Z0-9_\-]{20,}'), '[REDACTED_API_KEY]'),
    (re.compile(r'Bearer\s+[a-zA-Z0-9_\-\.]{16,}', re.IGNORECASE), 'Bearer [REDACTED_TOKEN]'),
    (re.compile(r'([a-zA-Z0-9]+:\/\/[^:\s]+:)([^@\s]+)(@)'), r'\1[REDACTED]\3'),
]


def _scrub_string(s: str) -> str:
    if not isinstance(s, str) or len(s) < 10:
        return s
    # Fast path: skip regex if no potential secret signature
    if not any(token in s for token in ("ey", "AKIA", "ghp_", "github_pat_", "sk-", "Bearer", "bearer", "://")):
        return s
    for pat, repl in SECRET_PATTERNS:
        s = pat.sub(repl, s)
    return s


def _scrub_secrets(obj: Any) -> Any:
    if isinstance(obj, str):
        return _scrub_string(obj)
    if isinstance(obj, dict):
        return {k: _scrub_secrets(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_scrub_secrets(item) for item in obj]
    return obj


def _safe_json_loads(val: Optional[str]) -> Optional[Any]:
    if not val:
        return None
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return None


# ─── Schema ──────────────────────────────────────────────────────────────
SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA busy_timeout = 5000;

CREATE TABLE IF NOT EXISTS sessions (
    id_hash TEXT PRIMARY KEY,
    id TEXT NOT NULL,
    state_json TEXT NOT NULL,
    updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at DESC);

CREATE TABLE IF NOT EXISTS kv (
    project TEXT NOT NULL,
    key TEXT NOT NULL,
    value_json TEXT NOT NULL,
    updated_at INTEGER NOT NULL,
    PRIMARY KEY (project, key)
);

CREATE TABLE IF NOT EXISTS facts (
    project TEXT NOT NULL,
    key TEXT NOT NULL,
    value_json TEXT NOT NULL,
    updated_at INTEGER NOT NULL,
    PRIMARY KEY (project, key)
);

CREATE TABLE IF NOT EXISTS memory (
    namespace TEXT NOT NULL,
    key TEXT NOT NULL,
    value_json TEXT NOT NULL,
    updated_at INTEGER NOT NULL,
    PRIMARY KEY (namespace, key)
);

CREATE TABLE IF NOT EXISTS index_docs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project TEXT NOT NULL,
    path TEXT NOT NULL,
    summary TEXT NOT NULL,
    tokens INTEGER DEFAULT 0,
    indexed_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_index_project ON index_docs(project);
"""


def _init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path, timeout=10.0)
    try:
        con.executescript(SCHEMA)
    finally:
        con.close()


def _connect(db_path: Optional[Path] = None) -> sqlite3.Connection:
    target = db_path or DB_PATH
    _init_db(target)
    return sqlite3.connect(target)


def _id_hash(session_id: str) -> str:
    return hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:32]


def _now() -> int:
    return int(time.time())


# ─── Session Store ───────────────────────────────────────────────────────
class SessionStore:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.home = self.db_path.parent
        _init_db(self.db_path)

    @contextmanager
    def _con(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.db_path, timeout=15.0, isolation_level=None)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA journal_mode = WAL;")
        con.execute("PRAGMA busy_timeout = 15000;")
        try:
            yield con
        finally:
            con.close()

    # ─── Session CRUD ──────────────────────────────────────────────────
    def create(self, session_id: str, title: str = "", goal: str = "") -> dict:
        state = {
            "id": session_id,
            "title": title or session_id,
            "goal": goal,
            "status": "active",
            "style": None,
            "global_style": None,
            "ponytail_mode": None,
            "checkpoints": [],
            "learned_facts": [],
            "created_at": _now(),
            "updated_at": _now(),
        }
        clean = _scrub_secrets(state)
        with self._con() as con:
            con.execute(
                "INSERT OR REPLACE INTO sessions (id_hash, id, state_json, updated_at) VALUES (?, ?, ?, ?)",
                (_id_hash(session_id), session_id, json.dumps(clean), state["updated_at"]),
            )
        return clean

    def load(self, session_id: str) -> Optional[dict]:
        with self._con() as con:
            row = con.execute(
                "SELECT state_json FROM sessions WHERE id_hash = ?", (_id_hash(session_id),)
            ).fetchone()
        if not row:
            return None
        data = _safe_json_loads(row["state_json"])
        return data if isinstance(data, dict) else None

    def save(
        self,
        session_id: str,
        *,
        done: str = "",
        next: str = "",
        style: Optional[str] = None,
        global_style: Optional[str] = None,
        ponytail_mode: Optional[str] = None,
        skill: Optional[str] = None,
        title: Optional[str] = None,
        goal: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict:
        state = self.load(session_id)
        if not isinstance(state, dict):
            state = self.create(session_id, title or "", goal or "")

        if not isinstance(state.get("checkpoints"), list):
            state["checkpoints"] = []

        if done or next:
            state["checkpoints"].append({
                "done": done,
                "next": next,
                "skill": skill,
                "timestamp": _now(),
            })
            state["checkpoints"] = state["checkpoints"][-20:]

        if style is not None:
            state["style"] = style
        if global_style is not None:
            state["global_style"] = global_style
        if ponytail_mode is not None:
            state["ponytail_mode"] = ponytail_mode
        if title is not None:
            state["title"] = title
        if goal is not None:
            state["goal"] = goal
        if status is not None:
            state["status"] = status

        state["updated_at"] = _now()
        clean = _scrub_secrets(state)
        with self._con() as con:
            con.execute(
                "INSERT OR REPLACE INTO sessions (id_hash, id, state_json, updated_at) VALUES (?, ?, ?, ?)",
                (_id_hash(session_id), session_id, json.dumps(clean), clean["updated_at"]),
            )
        return clean

    def mark_done(self, session_id: str) -> dict:
        return self.save(session_id, status="done")

    def delete(self, session_id: str) -> bool:
        with self._con() as con:
            cur = con.execute("DELETE FROM sessions WHERE id_hash = ?", (_id_hash(session_id),))
        return cur.rowcount > 0

    def list(self) -> List[dict]:
        with self._con() as con:
            rows = con.execute(
                "SELECT state_json FROM sessions ORDER BY updated_at DESC"
            ).fetchall()
        out = []
        for row in rows:
            s = _safe_json_loads(row["state_json"])
            if isinstance(s, dict) and "id" in s:
                out.append({
                    "id": s["id"],
                    "title": s.get("title", ""),
                    "goal": s.get("goal", ""),
                    "status": s.get("status", "active"),
                    "updated_at": s.get("updated_at", 0),
                })
        return out

    def get_or_create(self, session_id: str, title: str = "", goal: str = "") -> dict:
        state = self.load(session_id)
        if isinstance(state, dict):
            return state
        return self.create(session_id, title, goal)

    # ─── Project KV Store ──────────────────────────────────────────────
    def kv_set(self, project: str, key: str, value: Any) -> None:
        clean = _scrub_secrets(value)
        with self._con() as con:
            con.execute(
                "INSERT OR REPLACE INTO kv (project, key, value_json, updated_at) VALUES (?, ?, ?, ?)",
                (project, key, json.dumps(clean), _now()),
            )

    def kv_get(self, project: str, key: str) -> Any:
        with self._con() as con:
            row = con.execute(
                "SELECT value_json FROM kv WHERE project = ? AND key = ?", (project, key)
            ).fetchone()
        return _safe_json_loads(row["value_json"]) if row else None

    def kv_delete(self, project: str, key: str) -> bool:
        with self._con() as con:
            cur = con.execute("DELETE FROM kv WHERE project = ? AND key = ?", (project, key))
        return cur.rowcount > 0

    def kv_list(self, project: str) -> List[str]:
        with self._con() as con:
            rows = con.execute("SELECT key FROM kv WHERE project = ?", (project,)).fetchall()
        return [r["key"] for r in rows]

    # ─── Repo Micro-Skills & Fact Bank (SP fact / TokenEconomizer) ─────
    def fact_set(self, project: str, key: str, value: Any) -> None:
        """Store a durable repository fact."""
        clean = _scrub_secrets(value)
        with self._con() as con:
            con.execute(
                "INSERT OR REPLACE INTO facts (project, key, value_json, updated_at) VALUES (?, ?, ?, ?)",
                (project, key, json.dumps(clean), _now()),
            )

    def fact_get(self, project: str, key: str) -> Optional[Any]:
        """Retrieve a repository fact."""
        with self._con() as con:
            row = con.execute(
                "SELECT value_json FROM facts WHERE project = ? AND key = ?", (project, key)
            ).fetchone()
        return _safe_json_loads(row["value_json"]) if row else None

    def fact_list(self, project: str) -> Dict[str, Any]:
        """List all verified repository facts for a project."""
        with self._con() as con:
            rows = con.execute(
                "SELECT key, value_json FROM facts WHERE project = ?", (project,)
            ).fetchall()
        out = {}
        for r in rows:
            val = _safe_json_loads(r["value_json"])
            if val is not None:
                out[r["key"]] = val
        return out

    def fact_delete(self, project: str, key: str) -> bool:
        """Remove a repository fact."""
        with self._con() as con:
            cur = con.execute("DELETE FROM facts WHERE project = ? AND key = ?", (project, key))
        return cur.rowcount > 0

    # ─── Cross-Agent Memory ────────────────────────────────────────────
    def memory_write(self, namespace: str, key: str, value: Any) -> None:
        clean = _scrub_secrets(value)
        with self._con() as con:
            con.execute(
                "INSERT OR REPLACE INTO memory (namespace, key, value_json, updated_at) VALUES (?, ?, ?, ?)",
                (namespace, key, json.dumps(clean), _now()),
            )

    def memory_read(self, namespace: str, key: str) -> Any:
        with self._con() as con:
            row = con.execute(
                "SELECT value_json FROM memory WHERE namespace = ? AND key = ?", (namespace, key)
            ).fetchone()
        return _safe_json_loads(row["value_json"]) if row else None

    # ─── Semantic Search Index ─────────────────────────────────────────
    def index_write(self, project: str, docs: List[Dict[str, Any]]) -> None:
        with self._con() as con:
            con.execute("DELETE FROM index_docs WHERE project = ?", (project,))
            for doc in docs:
                con.execute(
                    "INSERT INTO index_docs (project, path, summary, tokens, indexed_at) VALUES (?, ?, ?, ?, ?)",
                    (project, doc["path"], doc["summary"], doc.get("tokens", 0), _now()),
                )

    def index_query(self, project: str, query: str, k: int = 3) -> List[Dict[str, Any]]:
        query_terms = set(query.lower().split())
        with self._con() as con:
            rows = con.execute(
                "SELECT path, summary, tokens FROM index_docs WHERE project = ?", (project,)
            ).fetchall()
        scored = []
        for row in rows:
            summary_terms = set(row["summary"].lower().split())
            overlap = len(query_terms & summary_terms)
            if overlap > 0:
                scored.append((overlap, dict(row)))
        scored.sort(key=lambda x: -x[0])
        return [
            {"path": d["path"], "snippet": d["summary"][:200], "score": s}
            for s, d in scored[:k]
        ]


# ─── Singleton ───────────────────────────────────────────────────────────
_default_store: Optional[SessionStore] = None


def get_store() -> SessionStore:
    global _default_store
    if _default_store is None:
        _default_store = SessionStore()
    return _default_store


# ─── CLI ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    store = get_store()

    if len(sys.argv) < 2:
        print("Usage: python sqlite.py <command> [args...]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "create":
        sid = sys.argv[2] if len(sys.argv) > 2 else f"test-{_now()}"
        print(json.dumps(store.create(sid), indent=1))
    elif cmd == "load":
        sid = sys.argv[2]
        print(json.dumps(store.load(sid), indent=1))
    elif cmd == "save":
        sid = sys.argv[2]
        done = sys.argv[3] if len(sys.argv) > 3 else ""
        nxt = sys.argv[4] if len(sys.argv) > 4 else ""
        print(json.dumps(store.save(sid, done=done, next=nxt), indent=1))
    elif cmd == "list":
        print(json.dumps(store.list(), indent=1))
    elif cmd == "delete":
        sid = sys.argv[2]
        print(store.delete(sid))
    elif cmd == "mark-done":
        sid = sys.argv[2]
        print(json.dumps(store.mark_done(sid), indent=1))
    elif cmd == "kv-set":
        proj, key, val = sys.argv[2], sys.argv[3], sys.argv[4]
        store.kv_set(proj, key, json.loads(val))
        print("ok")
    elif cmd == "kv-get":
        proj, key = sys.argv[2], sys.argv[3]
        print(json.dumps(store.kv_get(proj, key)))
    elif cmd == "index-write":
        proj = sys.argv[2]
        docs = json.loads(sys.argv[3])
        store.index_write(proj, docs)
        print("ok")
    elif cmd == "index-query":
        proj, query = sys.argv[2], sys.argv[3]
        print(json.dumps(store.index_query(proj, query), indent=1))
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
