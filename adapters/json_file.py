#!/usr/bin/env python3
"""
Session Pilot Pro Plus — JSON File Storage Adapter
====================================================
Drop-in persistence for OpenCode, Claude Code, Codex CLI, Cursor, Gemini CLI.
Zero dependencies, stdlib only, Python 3.8+.
"""

import json
import os
import re
import time
import uuid
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# ─── Config ──────────────────────────────────────────────────────────────
DEFAULT_HOME = Path.home() / ".session-pilot-pro-plus"
HOME = Path(os.environ.get("SESSION_PILOT_HOME", DEFAULT_HOME))
HOME.mkdir(parents=True, exist_ok=True)

SESSIONS_DIR = HOME / "sessions"
KV_DIR = HOME / "kv"
FACTS_DIR = HOME / "facts"
MEMORY_DIR = HOME / "memory"
INDEX_DIR = HOME / "index"

for d in [SESSIONS_DIR, KV_DIR, FACTS_DIR, MEMORY_DIR, INDEX_DIR]:
    d.mkdir(parents=True, exist_ok=True)


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


def _safe_component(name: str) -> str:
    """Sanitize path component to prevent path traversal and Windows invalid filenames."""
    if not name:
        return "_empty"
    h = hashlib.sha256(name.encode("utf-8")).hexdigest()[:16]
    clean = re.sub(r'[\x00-\x1f\\/:*?"<>|]+', '_', name).strip('. ')[:32]
    return f"{clean}_{h}" if clean else f"_{h}"


# ─── Helpers ─────────────────────────────────────────────────────────────
def _session_path(session_id: str, base: Optional[Path] = None) -> Path:
    safe = hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:16]
    base = base or SESSIONS_DIR
    return base / f"{safe}.json"


def _now() -> int:
    return int(time.time())


def _atomic_write(path: Path, data: Any) -> None:
    """Write JSON atomically using UUID tmp file and exponential backoff retry."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / f"{path.stem}.{uuid.uuid4().hex[:8]}.tmp"
    clean_data = _scrub_secrets(data)
    content = json.dumps(clean_data, ensure_ascii=False, indent=1)
    tmp.write_text(content, encoding="utf-8")
    for attempt in range(8):
        try:
            os.replace(tmp, path)
            return
        except OSError:
            if attempt == 7:
                try:
                    if path.exists():
                        path.unlink(missing_ok=True)
                    os.replace(tmp, path)
                    return
                except Exception:
                    pass
                if tmp.exists():
                    try:
                        tmp.unlink(missing_ok=True)
                    except Exception:
                        pass
                raise
            time.sleep(0.005 * (2 ** attempt))


def _read_json(path: Path) -> Optional[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, (dict, list)) else None
    except (OSError, json.JSONDecodeError, TypeError):
        return None


# ─── Session Store ───────────────────────────────────────────────────────
class SessionStore:
    """High-level session API used by the agent on SP save / SP recall."""

    def __init__(self, home: Optional[Path] = None):
        self.home = home or HOME
        self.sessions_dir = self.home / "sessions"
        self.kv_dir = self.home / "kv"
        self.facts_dir = self.home / "facts"
        self.memory_dir = self.home / "memory"
        self.index_dir = self.home / "index"
        for d in [self.sessions_dir, self.kv_dir, self.facts_dir, self.memory_dir, self.index_dir]:
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
            "ponytail_mode": None,
            "checkpoints": [],
            "learned_facts": [],
            "created_at": _now(),
            "updated_at": _now(),
        }
        _atomic_write(_session_path(session_id, base=self.sessions_dir), state)
        return state

    def load(self, session_id: str) -> Optional[dict]:
        """Load session state or None if not found or malformed."""
        state = _read_json(_session_path(session_id, base=self.sessions_dir))
        if not isinstance(state, dict):
            return None
        return state

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
        """Append a checkpoint; update optional fields."""
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
            # Keep last 20 checkpoints
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
            if isinstance(s, dict) and "id" in s:
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
        if isinstance(state, dict):
            return state
        return self.create(session_id, title, goal)

    # ─── Project KV Store (SP persist) ──────────────────────────────────
    def kv_set(self, project: str, key: str, value: Any) -> None:
        """Store a small JSON value per project."""
        safe_proj = _safe_component(project)
        safe_key = _safe_component(key)
        proj_dir = self.kv_dir / safe_proj
        proj_dir.mkdir(parents=True, exist_ok=True)
        _atomic_write(proj_dir / f"{safe_key}.json", {"key": key, "value": value, "updated_at": _now()})

    def kv_get(self, project: str, key: str) -> Any:
        safe_proj = _safe_component(project)
        safe_key = _safe_component(key)
        p = self.kv_dir / safe_proj / f"{safe_key}.json"
        data = _read_json(p)
        return data["value"] if (isinstance(data, dict) and "value" in data) else None

    def kv_delete(self, project: str, key: str) -> bool:
        safe_proj = _safe_component(project)
        safe_key = _safe_component(key)
        p = self.kv_dir / safe_proj / f"{safe_key}.json"
        if p.exists():
            p.unlink()
            return True
        return False

    def kv_list(self, project: str) -> List[str]:
        safe_proj = _safe_component(project)
        proj_dir = self.kv_dir / safe_proj
        if not proj_dir.exists():
            return []
        keys = []
        for f in proj_dir.glob("*.json"):
            data = _read_json(f)
            if isinstance(data, dict) and "key" in data:
                keys.append(data["key"])
            else:
                keys.append(f.stem)
        return keys

    # ─── Repo Micro-Skills & Fact Bank (SP fact / TokenEconomizer) ─────
    def fact_set(self, project: str, key: str, value: Any) -> None:
        """Store a durable repository fact (build/test command, linter, path alias)."""
        safe_proj = _safe_component(project)
        safe_key = _safe_component(key)
        proj_dir = self.facts_dir / safe_proj
        proj_dir.mkdir(parents=True, exist_ok=True)
        _atomic_write(proj_dir / f"{safe_key}.json", {"key": key, "value": value, "updated_at": _now()})

    def fact_get(self, project: str, key: str) -> Optional[Any]:
        """Retrieve a repository fact."""
        safe_proj = _safe_component(project)
        safe_key = _safe_component(key)
        p = self.facts_dir / safe_proj / f"{safe_key}.json"
        data = _read_json(p)
        return data["value"] if (isinstance(data, dict) and "value" in data) else None

    def fact_list(self, project: str) -> Dict[str, Any]:
        """List all verified repository facts for a project."""
        safe_proj = _safe_component(project)
        proj_dir = self.facts_dir / safe_proj
        if not proj_dir.exists():
            return {}
        facts = {}
        for f in proj_dir.glob("*.json"):
            data = _read_json(f)
            if isinstance(data, dict) and "key" in data and "value" in data:
                facts[data["key"]] = data["value"]
        return facts

    def fact_delete(self, project: str, key: str) -> bool:
        """Remove a repository fact."""
        safe_proj = _safe_component(project)
        safe_key = _safe_component(key)
        p = self.facts_dir / safe_proj / f"{safe_key}.json"
        if p.exists():
            p.unlink()
            return True
        return False

    # ─── Cross-Agent Memory (SP memory sync) ────────────────────────────
    def memory_write(self, namespace: str, key: str, value: Any) -> None:
        safe_ns = _safe_component(namespace)
        safe_key = _safe_component(key)
        ns_dir = self.memory_dir / safe_ns
        ns_dir.mkdir(parents=True, exist_ok=True)
        _atomic_write(ns_dir / f"{safe_key}.json", {"key": key, "value": value, "updated_at": _now()})

    def memory_read(self, namespace: str, key: str) -> Any:
        safe_ns = _safe_component(namespace)
        safe_key = _safe_component(key)
        p = self.memory_dir / safe_ns / f"{safe_key}.json"
        data = _read_json(p)
        return data["value"] if (isinstance(data, dict) and "value" in data) else None

    # ─── Semantic Search Index (SP index / SP query) ────────────────────
    def index_write(self, project: str, docs: List[Dict[str, Any]]) -> None:
        """Store searchable summaries. Each doc: {path, summary, tokens}."""
        safe_proj = _safe_component(project)
        proj_dir = self.index_dir / safe_proj
        proj_dir.mkdir(parents=True, exist_ok=True)
        for i, doc in enumerate(docs):
            _atomic_write(proj_dir / f"{i:06d}.json", {
                "path": doc["path"],
                "summary": doc["summary"],
                "tokens": doc.get("tokens", 0),
                "indexed_at": _now(),
            })

    def index_query(self, project: str, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Simple keyword overlap search (no embeddings)."""
        safe_proj = _safe_component(project)
        proj_dir = self.index_dir / safe_proj
        if not proj_dir.exists():
            return []
        query_terms = set(query.lower().split())
        scored = []
        for f in proj_dir.glob("*.json"):
            doc = _read_json(f)
            if not isinstance(doc, dict):
                continue
            summary_terms = set(doc.get("summary", "").lower().split())
            overlap = len(query_terms & summary_terms)
            if overlap > 0:
                scored.append((overlap, doc))
        scored.sort(key=lambda x: -x[0])
        return [
            {"path": d.get("path", ""), "snippet": d.get("summary", "")[:200], "score": s}
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
