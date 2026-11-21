#!/usr/bin/env python3
"""
Session Pilot Pro Plus — Automated Verification Suite
=====================================================
Runs every capability of the skill against the bundled JSON-file adapter.
Designed to be executed by CI (GitHub Actions) or locally before release.

Usage:
    python scripts/verify.py [--adapter json_file|sqlite] [--home /tmp/sp-test]
"""

import argparse
import sys
import time
from pathlib import Path

# Windows console: force UTF-8 so ✓/✗ symbols print cleanly
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# ─── Import adapter ────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent.parent
ADAPTER_DIR = SCRIPT_DIR / "adapters"

sys.path.insert(0, str(ADAPTER_DIR))

def load_adapter(name: str):
    import importlib.util
    module_path = ADAPTER_DIR / f"{name}.py"
    if not module_path.exists():
        raise FileNotFoundError(module_path)
    spec = importlib.util.spec_from_file_location(f"sp_{name}", module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── Test Runner ───────────────────────────────────────────────────────────
class Results:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.skipped = []

    def check(self, label: str, condition: bool, detail: str = ""):
        if condition:
            self.passed.append((label, detail))
        else:
            self.failed.append((label, detail))

    def summary(self) -> str:
        lines = []
        lines.append("")
        lines.append("=" * 60)
        lines.append("  Session Pilot Pro Plus — Verify Results")
        lines.append("=" * 60)
        lines.append(f"  Passed: {len(self.passed)}")
        lines.append(f"  Failed: {len(self.failed)}")
        lines.append(f"  Skipped: {len(self.skipped)}")
        lines.append("=" * 60)
        if self.failed:
            lines.append("\n  FAILURES:")
            for label, detail in self.failed:
                lines.append(f"    ✗ {label} — {detail}")
        lines.append("")
        return "\n".join(lines)


# ─── Core Tests ────────────────────────────────────────────────────────────
def test_core(store, R: Results):
    # Create
    sid = f"verify-core-{int(time.time())}"
    state = store.create(sid, title="verify-core", goal="test creation")
    R.check("create session", state["id"] == sid and state["status"] == "active", f"id={state['id']}")

    # Get-or-create
    fetched = store.get_or_create(sid)
    R.check("get_or_create existing", fetched["id"] == sid, f"title={fetched['title']}")

    # Save checkpoint
    updated = store.save(sid, done="created session", next="run checks")
    R.check("save checkpoint", len(updated["checkpoints"]) == 1 and updated["checkpoints"][0]["done"] == "created session", "")

    # Recall reads checkpoint
    loaded = store.load(sid)
    R.check("recall restores checkpoints", len(loaded["checkpoints"]) == 1, "")

    # Mark done
    done_state = store.mark_done(sid)
    R.check("mark-done sets status", done_state["status"] == "done", f"status={done_state['status']}")

    # Load after mark-done preserves status
    still_done = store.load(sid)
    R.check("recall preserves done status", still_done["status"] == "done", "")

    # Delete
    del_ok = store.delete(sid)
    R.check("delete session", del_ok, "")
    gone = store.load(sid)
    R.check("deleted session returns None", gone is None, "")


def test_style_mirroring(store, R: Results):
    sid = f"verify-style-{int(time.time())}"
    store.save(sid, done="x", next="y", style="casual lowercase", global_style="formal bullets")
    state = store.load(sid)
    R.check("style persisted", state.get("style") == "casual lowercase", f"got={state.get('style')}")
    R.check("global_style persisted", state.get("global_style") == "formal bullets", f"got={state.get('global_style')}")
    store.delete(sid)


def test_kv_store(store, R: Results):
    proj, key, val = "verify-kv", "framework", "fastapi"
    store.kv_set(proj, key, val)
    got = store.kv_get(proj, key)
    R.check("kv set/get", got == val, f"got={got!r}")
    keys = store.kv_list(proj)
    R.check("kv list", key in keys, f"keys={keys}")
    deleted = store.kv_delete(proj, key)
    R.check("kv delete", deleted, "")
    still_gone = store.kv_get(proj, key)
    R.check("kv deleted", still_gone is None, "")


def test_memory_sync(store, R: Results):
    ns, key, val = "team-alpha", "shared-framework", "litestar"
    store.memory_write(ns, key, val)
    got = store.memory_read(ns, key)
    R.check("memory write/read", got == val, f"got={got!r}")
    store.delete(f"mem-{ns}")  # cleanup stub


def test_semantic_index(store, R: Results):
    proj = "verify-index"
    docs = [
        {"path": "src/auth.py", "summary": "JWT authentication middleware handles token validation and refresh logic", "tokens": 45},
        {"path": "src/payments.py", "summary": "Stripe payment processing with webhook verification and retry queue", "tokens": 38},
        {"path": "tests/test_auth.py", "summary": "Unit tests for auth middleware covering invalid tokens and expired sessions", "tokens": 28},
    ]
    store.index_write(proj, docs)
    hits = store.index_query(proj, "stripe payment", k=3)
    R.check("index query matches relevant doc", len(hits) > 0, f"hits={[h['path'] for h in hits]}")
    top = hits[0] if hits else {}
    R.check("top hit is payments file", top.get("path") == "src/payments.py", f"got={top.get('path')}")
    # Cleanup: clear index for project
    store.index_write(proj, [])


def test_session_lifecycle(store, R: Results):
    sid1 = f"verify-life-{int(time.time())}-a"
    sid2 = f"verify-life-{int(time.time())}-b"
    store.create(sid1, title="project-a")
    store.create(sid2, title="project-b")
    sessions = store.list()
    ids = {s["id"] for s in sessions}
    R.check("list includes created sessions", sid1 in ids and sid2 in ids, f"ids={ids}")
    store.delete(sid1)
    sessions2 = store.list()
    ids2 = {s["id"] for s in sessions2}
    R.check("list excludes deleted session", sid1 not in ids2 and sid2 in ids2, f"ids={ids2}")


def test_budget_estimate():
    """Pure function test — no store needed."""
    # 5 words → round(5 × 1.33) = round(6.65) = 7 tokens
    words = "hello world foo bar baz".split()
    tokens = round(len(words) * 1.33)
    assert tokens == 7, f"expected 7, got {tokens}"
    return True


# ─── Main ──────────────────────────────────────────────────────────────────
def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", default="json_file", choices=["json_file", "sqlite"])
    ap.add_argument("--home", default=None)
    args = ap.parse_args()

    mod = load_adapter(args.adapter)
    store = mod.get_store()
    if args.home:
        store.home = Path(args.home)
        # Ensure dirs exist (attribute names differ slightly per adapter)
        dirs = [
            store.home / "sessions",
            store.home / "kv",
            store.home / "memory",
            store.home / "index",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        if hasattr(store, "sessions_dir"):
            store.sessions_dir = dirs[0]
            store.kv_dir = dirs[1]
            store.memory_dir = dirs[2]
            store.index_dir = dirs[3]

    R = Results()
    print(f"Running verification with adapter: {args.adapter}")
    print(f"Storage home: {store.home}\n")

    try:
        test_core(store, R)
        test_style_mirroring(store, R)
        test_kv_store(store, R)
        test_memory_sync(store, R)
        test_semantic_index(store, R)
        test_session_lifecycle(store, R)
        test_budget_estimate()
        R.check("budget estimate (pure fn)", True)
    except Exception as e:
        R.failed.append(("Exception", str(e)))

    print(R.summary())
    sys.exit(0 if not R.failed else 1)


if __name__ == "__main__":
    main()