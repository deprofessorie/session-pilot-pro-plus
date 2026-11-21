# Storage Adapters for Session Pilot Pro Plus

Since Session Pilot Pro Plus is prompt-only, **persistence requires the host agent to implement a storage adapter**. This document defines the interface so any agent can plug in real storage (file, SQLite, KV store, etc.) and make `SP save` / `SP recall` survive context truncation.

---

## The Adapter Interface

An adapter is a small module the agent loads at startup. It exposes these async functions:

```typescript
interface StorageAdapter {
  // Session lifecycle
  createSession(id: string, initialState: SessionState): Promise<void>;
  getSession(id: string): Promise<SessionState | null>;
  updateSession(id: string, patch: Partial<SessionState>): Promise<void>;
  deleteSession(id: string): Promise<void>;
  listSessions(): Promise<SessionSummary[]>;

  // Key-value store (for SP persist)
  kvSet(project: string, key: string, value: unknown): Promise<void>;
  kvGet(project: string, key: string): Promise<unknown | null>;
  kvDelete(project: string, key: string): Promise<void>;
  kvList(project: string): Promise<string[]>;

  // Cross-agent memory (for SP memory sync)
  memoryWrite(namespace: string, key: string, value: unknown): Promise<void>;
  memoryRead(namespace: string, key: string): Promise<unknown | null>;

  // Semantic search index (for SP index / SP query)
  indexWrite(project: string, docs: IndexDoc[]): Promise<void>;
  indexQuery(project: string, query: string, k?: number): Promise<IndexHit[]>;

  // Optional: background indexing hook
  onFileChange?(path: string): Promise<void>;
}

interface SessionState {
  id: string;
  title: string;
  goal: string;
  status: "active" | "done";
  style?: string;
  globalStyle?: string;
  checkpoints: Checkpoint[];
  learnedFacts: Fact[];
  createdAt: number;
  updatedAt: number;
}

interface SessionSummary {
  id: string;
  title: string;
  goal: string;
  status: "active" | "done";
  updatedAt: number;
}

interface Checkpoint {
  done: string;
  next: string;
  skill?: string;
  timestamp: number;
}

interface Fact {
  text: string;
  source: "checkpoint" | "review" | "manual";
  timestamp: number;
}

interface IndexDoc {
  path: string;
  summary: string;
  tokens: number;
}

interface IndexHit {
  path: string;
  snippet: string;
  score: number;
}
```

---

## Built-in Adapters (Reference Implementations)

### 1. JSON File Adapter (simplest, works everywhere)

```python
# ~/.config/opencode/skills/session-pilot-pro-plus/adapters/json_file.py
import json, os, time
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE = Path(os.environ.get("SESSION_PILOT_HOME", Path.home() / ".session-pilot-pro-plus"))
BASE.mkdir(parents=True, exist_ok=True)

SESSIONS = BASE / "sessions"
KV = BASE / "kv"
MEMORY = BASE / "memory"
INDEX = BASE / "index"

for d in [SESSIONS, KV, MEMORY, INDEX]:
    d.mkdir(exist_ok=True)

def _session_path(id: str) -> Path:
    return SESSIONS / f"{id}.json"

def create_session(id: str, state: Dict) -> None:
    state["createdAt"] = state.get("createdAt", int(time.time()))
    state["updatedAt"] = int(time.time())
    _session_path(id).write_text(json.dumps(state, ensure_ascii=False, indent=1))

def get_session(id: str) -> Optional[Dict]:
    p = _session_path(id)
    return json.loads(p.read_text()) if p.exists() else None

def update_session(id: str, patch: Dict) -> None:
    s = get_session(id)
    if s:
        s.update(patch)
        s["updatedAt"] = int(time.time())
        create_session(id, s)

def delete_session(id: str) -> None:
    _session_path(id).unlink(missing_ok=True)

def list_sessions() -> List[Dict]:
    out = []
    for f in SESSIONS.glob("*.json"):
        s = json.loads(f.read_text())
        out.append({
            "id": s["id"],
            "title": s.get("title", ""),
            "goal": s.get("goal", ""),
            "status": s.get("status", "active"),
            "updatedAt": s.get("updatedAt", 0),
        })
    return sorted(out, key=lambda x: -x["updatedAt"])

def kv_set(project: str, key: str, value: Any) -> None:
    (KV / project).mkdir(exist_ok=True)
    (KV / project / f"{key}.json").write_text(json.dumps(value))

def kv_get(project: str, key: str) -> Any:
    p = KV / project / f"{key}.json"
    return json.loads(p.read_text()) if p.exists() else None

# ... memory, index methods similar
```

**Usage:** Agent loads this module on startup, calls functions when `SP save` / `SP recall` are invoked.

---

### 2. SQLite Adapter (better for concurrent access)

```python
# ~/.config/opencode/skills/session-pilot-pro-plus/adapters/sqlite.py
import sqlite3, json, time, os
from pathlib import Path
from typing import Any, Dict, List, Optional

DB = Path(os.environ.get("SESSION_PILOT_HOME", Path.home() / ".session-pilot-pro-plus")) / "storage.db"

def _init():
    con = sqlite3.connect(DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            state_json TEXT NOT NULL,
            updated_at INTEGER NOT NULL
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS kv (
            project TEXT, key TEXT, value_json TEXT,
            PRIMARY KEY (project, key)
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            namespace TEXT, key TEXT, value_json TEXT,
            PRIMARY KEY (namespace, key)
        )
    """)
    con.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS index_docs USING fts5(
            project, path, summary, tokens, content=index_docs
        )
    """)
    con.commit()
    return con

def create_session(id: str, state: Dict):
    con = _init()
    state["createdAt"] = state.get("createdAt", int(time.time()))
    state["updatedAt"] = int(time.time())
    con.execute("INSERT OR REPLACE INTO sessions VALUES (?, ?, ?)",
                (id, json.dumps(state), state["updatedAt"]))
    con.commit()
```

---

### 3. UPSTASH / Cloudflare KV Adapter (serverless, shared across agents)

```typescript
// For agents running in serverless/edge environments
import { Redis } from "@upstash/redis";

const redis = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL!,
  token: process.env.UPSTASH_REDIS_REST_TOKEN!,
});

export const upstashAdapter = {
  async createSession(id: string, state: SessionState) {
    await redis.set(`sp:session:${id}`, JSON.stringify(state));
  },
  async getSession(id: string) {
    const v = await redis.get(`sp:session:${id}`);
    return v ? JSON.parse(v as string) : null;
  },
  // ... etc
};
```

---

### 4. IndexedDB Adapter (browser-based agents)

```javascript
// For web-based agents (ChatGPT, Claude.ai, etc.)
const DB_NAME = "session-pilot-pro-plus";

function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = (e) => {
      const db = e.target.result;
      db.createObjectStore("sessions", { keyPath: "id" });
      db.createObjectStore("kv", { keyPath: ["project", "key"] });
      db.createObjectStore("memory", { keyPath: ["namespace", "key"] });
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

export const indexedDBAdapter = {
  async createSession(id, state) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction("sessions", "readwrite");
      tx.objectStore("sessions").put({ ...state, id });
      tx.oncomplete = resolve;
      tx.onerror = () => reject(tx.error);
    });
  },
  // ...
};
```

---

## How Agents Should Wire It

### OpenCode (has file access, runs Python)

```python
# In AGENTS.md or skill bootstrap:
# Load the JSON file adapter on startup
import sys
sys.path.append("~/.config/opencode/skills/session-pilot-pro-plus/adapters")
from json_file import create_session, get_session, update_session, ...

# When user says "SP save ...", call update_session(...)
# When user says "SP recall ...", call get_session(...) and inject into context
```

### Claude Code (has file access via tools)

```markdown
# In ~/.claude/CLAUDE.md or project CLAUDE.md
# The agent reads/writes ~/.session-pilot-pro-plus/sessions/*.json directly
# Use Bash tool to invoke the Python adapter module
```

### Codex CLI / Cursor (has file access)

```markdown
# Similar to OpenCode — agent runs the adapter module via shell
```

### Web Agents (no file access)

```markdown
# In custom instructions:
# Use the IndexedDB adapter. On SP save, write to IndexedDB.
# On SP recall, read from IndexedDB and prepend to context.
```

---

## Minimal Viable Adapter (for agents that can only do key-value)

If the agent only has a simple KV store (e.g., `localStorage`, `chrome.storage`, a single JSON file), implement just:

```typescript
interface MinimalAdapter {
  saveSession(id: string, state: SessionState): Promise<void>;
  loadSession(id: string): Promise<SessionState | null>;
  listSessions(): Promise<SessionSummary[]>;
  deleteSession(id: string): Promise<void>;
}
```

This covers 90% of use cases (recall, save, list, delete). The rest (KV, memory, index) are opt-in.

---

## Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `SESSION_PILOT_HOME` | Root directory for file-based adapters | `~/.session-pilot-pro-plus` |
| `SESSION_PILOT_ADAPTER` | Adapter module to load (`json_file`, `sqlite`, `upstash`, `indexeddb`) | `json_file` |
| `SESSION_PILOT_ID` | Forced session ID when `--session` omitted | — |

---

## Testing an Adapter

Run these commands in order; all should work without errors:

```text
SP recall --create "test-session"
SP save --done "wrote adapter" --next "verify recall"
SP recall --session "test-session"
SP recall --list
SP recall --delete "test-session"
SP recall --list
```

Expected: session appears in list after create, state restores on recall, disappears after delete.

---

## Contributing Adapters

1. Add `adapters/<name>.py` (or `.ts`/`.js`) to the skill folder
2. Implement the full `StorageAdapter` interface
3. Add a one-line entry to `ADAPTERS.md` (this file) under "Built-in Adapters"
4. Test with the sequence above
5. PR with description of target environment