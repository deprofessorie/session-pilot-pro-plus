#!/usr/bin/env python3
"""
Session Pilot Pro Plus — JSON File Storage Adapter
====================================================
Drop-in persistence for OpenCode, Claude Code, Codex CLI, Cursor, Gemini CLI.
Zero dependencies, stdlib only, Python 3.8+.

Usage (in your AGENTS.md / CLAUDE.md / AGENTS.md):
    import sys
    sys.path.append("~/.config/opencode/skills/session-pilot-pro-plus/adapters")
    from json_file import SessionStore
    store = SessionStore()

    # On SP save:
    store.save(session_id, done="...", next="...", style="...", skill="...")

    # On SP recall:
    state = store.load(session_id)
    # inject state into context
"""

import json
import os
import time
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# ─── Config ──────────────────────────────────────────────────────────────
DEFAULT_HOME = Path.home() / ".session-pilot-pro-plus"
HOME = Path(os.environ.get("SESSION_PILOT_HOME", DEFAULT_HOME))
HOME.mkdir(parents=True, exist_ok=True)

SESSIONS_DIR = HOME / "sessions"
KV_DIR = HOME / "kv"
MEMORY_DIR = HOME / "memory"
INDEX_DIR = HOME / "index"

for d in [SESSIONS_DIR, KV_DIR, MEMORY_DIR, INDEX_DIR]:
    d.mkdir(exist_ok=True)


# ─── Helpers ─────────────────────────────────────────────────────────────
def _session_path(session_id: str, base: Optional[Path] = None) -> Path:
    """Return the file path for a session ID.
    
    Args:
        session_id: The session identifier.
        base: Optional base directory (defaults to module-level SESSIONS_DIR).
    """
    safe = hashlib.sha256(session_id.encode()).hexdigest()[:16]
    base = base or SESSIONS_DIR
    return base / f"{safe}.json"


def _now() -> int:
    return int(time.time())


def _atomic_write(path: Path, data: dict) -> None:
    """Write JSON atomically (tmp + rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def _read_json(path: Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


# ─── Session Store ───────────────────────────────────────────────────────
class SessionStore:
    """High-level session API used by the agent on SP save / SP recall."""

    def __init__(self, home: Optional[Path] = None):
        self.home = home or HOME
        self.sessions_dir = self.home / "sessions"
        self.kv_dir = self.home / "kv"
        self.memory_dir = self.home / "memory"
        self.index_dir = self.home / "index"
        for d in [self.sessions_dir, self.kv_dir, self.memory_dir, self.index_dir]:
            d.mkdir(parents=True, exist_ok=True)

    # ─── Session CRUD ──────────────────────────────────────────────────
    def create(self, session_id: str, title: str = "", goal: str = "") -> dict:
        """Create a fresh session."""
        state = {
            "id": session_id,
            "title": title or session_id,
            "goal": goal,
            "status": "active",
            "style": None,
            "global_style": None,
            "checkpoints": [],
            "learned_facts": [],
            "created_at": _now(),
            "updated_at": _now(),
        }
        _atomic_write(_session_path(session_id, base=self.sessions_dir), state)
        return state

    def load(self, session_id: str) -> Optional[dict]:
        """Load session state or None if not found."""
        return _read_json(_session_path(session_id, base=self.sessions_dir))

    def save(
        self,
        session_id: str,
        *,
        done: str = "",
        next: str = "",
        style: Optional[str] = None,
        global_style: Optional[str] = None,
        skill: Optional[str] = None,
        title: Optional[str] = None,
        goal: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict:
        """Append a checkpoint; update optional fields."""
        state = self.load(session_id)
        if not state:
            state = self.create(session_id, title or "", goal or "")

        if done or next:
            state["checkpoints"].append({
                "done": done,
                "next": next,
                "skill": skill,
                "timestamp": _now(),
            })
            # Keep last 20 checkpoints
            state["checkpoints"] = state["checkpoints"][-20:]

        if style is not None:
            state["style"] = style
        if global_style is not None:
            state["global_style"] = global_style
        if title is not None:
            state["title"] = title
        if goal is not None:
            state["goal"] = goal
        if status is not None:
            state["status"] = status

        state["updated_at"] = _now()
        _atomic_write(_session_path(session_id, base=self.sessions_dir), state)
        return state

    def mark_done(self, session_id: str) -> dict:
        """Mark session complete."""
        return self.save(session_id, status="done")

    def delete(self, session_id: str) -> bool:
        """Delete a session."""
        p = _session_path(session_id, base=self.sessions_dir)
        if p.exists():
            p.unlink()
            return True
        return False

    def list(self) -> List[dict]:
        """All sessions, most recent first."""
        out = []
        for f in self.sessions_dir.glob("*.json"):
            s = _read_json(f)
            if s:
                out.append({
                    "id": s["id"],
                    "title": s.get("title", ""),
                    "goal": s.get("goal", ""),
                    "status": s.get("status", "active"),
                    "updated_at": s.get("updated_at", 0),
                })
        return sorted(out, key=lambda x: -x["updated_at"])

    def get_or_create(self, session_id: str, title: str = "", goal: str = "") -> dict:
        """Load existing or create new — used by SP recall --session."""
        state = self.load(session_id)
        if state:
            return state
        return self.create(session_id, title, goal)

    # ─── Project KV Store (SP persist) ──────────────────────────────────
    def kv_set(self, project: str, key: str, value: Any) -> None:
        """Store a small JSON value per project."""
        proj_dir = self.kv_dir / project
        proj_dir.mkdir(exist_ok=True)
        _atomic_write(proj_dir / f"{key}.json", {"value": value, "updated_at": _now()})

    def kv_get(self, project: str, key: str) -> Any:
        p = self.kv_dir / project / f"{key}.json"
        data = _read_json(p)
        return data["value"] if data else None

    def kv_delete(self, project: str, key: str) -> bool:
        p = self.kv_dir / project / f"{key}.json"
        if p.exists():
            p.unlink()
            return True
        return False

    def kv_list(self, project: str) -> List[str]:
        proj_dir = self.kv_dir / project
        if not proj_dir.exists():
            return []
        return [f.stem for f in proj_dir.glob("*.json")]

    # ─── Cross-Agent Memory (SP memory sync) ────────────────────────────
    def memory_write(self, namespace: str, key: str, value: Any) -> None:
        ns_dir = self.memory_dir / namespace
        ns_dir.mkdir(exist_ok=True)
        _atomic_write(ns_dir / f"{key}.json", {"value": value, "updated_at": _now()})

    def memory_read(self, namespace: str, key: str) -> Any:
        p = self.memory_dir / namespace / f"{key}.json"
        data = _read_json(p)
        return data["value"] if data else None

    # ─── Semantic Search Index (SP index / SP query) ────────────────────
    def index_write(self, project: str, docs: List[Dict[str, Any]]) -> None:
        """Store searchable summaries. Each doc: {path, summary, tokens}."""
        proj_dir = self.index_dir / project
        proj_dir.mkdir(exist_ok=True)
        for i, doc in enumerate(docs):
            _atomic_write(proj_dir / f"{i:06d}.json", {
                "path": doc["path"],
                "summary": doc["summary"],
                "tokens": doc.get("tokens", 0),
                "indexed_at": _now(),
            })

    def index_query(self, project: str, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Simple keyword overlap search (no embeddings)."""
        proj_dir = self.index_dir / project
        if not proj_dir.exists():
            return []
        query_terms = set(query.lower().split())
        scored = []
        for f in proj_dir.glob("*.json"):
            doc = _read_json(f)
            if not doc:
                continue
            summary_terms = set(doc["summary"].lower().split())
            overlap = len(query_terms & summary_terms)
            if overlap > 0:
                scored.append((overlap, doc))
        scored.sort(key=lambda x: -x[0])
        return [
            {"path": d["path"], "snippet": d["summary"][:200], "score": s}
            for s, d in scored[:k]
        ]


# ─── Convenience: Global Instance ───────────────────────────────────────
_default_store: Optional[SessionStore] = None


def get_store() -> SessionStore:
    """Singleton for simple imports."""
    global _default_store
    if _default_store is None:
        _default_store = SessionStore()
    return _default_store


# ─── CLI (for testing) ──────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    store = get_store()

    if len(sys.argv) < 2:
        print("Usage: python json_file.py <command> [args...]")
        print("Commands: create, load, save, list, delete, mark-done, kv-set, kv-get, index-write, index-query")
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