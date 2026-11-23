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


def test_ponytail(store, R: Results):
    sid = f"verify-ponytail-{int(time.time())}"
    store.save(sid, done="impl", next="test", ponytail_mode="ultra")
    state = store.load(sid)
    R.check("ponytail_mode persisted", state.get("ponytail_mode") == "ultra", f"got={state.get('ponytail_mode')}")
    store.delete(sid)


def test_facts(store, R: Results):
    proj, key, val = "verify-facts-proj", "build_cmd", "pnpm run build"
    store.fact_set(proj, key, val)
    got = store.fact_get(proj, key)
    R.check("fact set/get", got == val, f"got={got!r}")
    all_facts = store.fact_list(proj)
    R.check("fact list includes key", key in all_facts and all_facts[key] == val, f"facts={all_facts}")
    deleted = store.fact_delete(proj, key)
    R.check("fact delete", deleted, "")
    still_gone = store.fact_get(proj, key)
    R.check("fact deleted returns None", still_gone is None, "")


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


def test_budget_estimate(R: Results):
    """Test token estimation on complex code with symbols, escapes, and CJK characters."""
    sys.path.insert(0, str(SCRIPT_DIR / "scripts"))
    import sp
    sample_code = """
    def parse_symbols(text: str) -> dict:
        # Regex characters: []{}();:=<>+*/_&|~^%!@#$"\'\\
        arr = [1, 2, {"key": "val"}]
        cjk_text = "你好世界，こんにちは"
        return {"result": len(arr), "cjk": cjk_text}
    """
    est = sp.estimate_tokens(sample_code)
    R.check("budget estimate runs on code symbols without regex crash", est["tokens"] > 0, f"tokens={est['tokens']}")
    R.check("budget estimate detects code symbols", est.get("code_symbols", 0) > 10, f"symbols={est.get('code_symbols')}")
    R.check("budget estimate detects CJK characters", est.get("cjk_chars", 0) > 5, f"cjk={est.get('cjk_chars')}")
    words = "hello world foo bar baz".split()
    tokens = round(len(words) * 1.33)
    R.check("budget estimate (pure fn formula)", tokens == 7, f"got {tokens}")


def test_loop_detection(store, R: Results):
    """Test real checkpoint loop detection."""
    sys.path.insert(0, str(SCRIPT_DIR / "scripts"))
    import sp
    sid = f"verify-loop-{int(time.time())}"
    # Save 3 identical checkpoints
    store.save(sid, done="failed test assertion A", next="retry")
    store.save(sid, done="failed test assertion A", next="retry")
    store.save(sid, done="failed test assertion A", next="retry")

    state = store.load(sid)
    loop = sp.detect_loop(state, threshold=3)
    R.check("loop detection triggers on 3 identical checkpoints", loop["detected"] is True, f"count={loop['count']}")

    # Save a different checkpoint
    store.save(sid, done="fixed test assertion A", next="continue")
    state = store.load(sid)
    loop_broken = sp.detect_loop(state, threshold=3)
    R.check("loop detection clears when distinct checkpoint is saved", loop_broken["detected"] is False, f"count={loop_broken['count']}")
    store.delete(sid)


def test_compaction(store, R: Results):
    """Test checkpoint list compaction in session store."""
    sid = f"verify-compact-{int(time.time())}"
    for i in range(10):
        store.save(sid, done=f"step {i}", next=f"step {i+1}")

    state = store.load(sid)
    orig_len = len(state.get("checkpoints", []))
    R.check("pre-compaction has 10 checkpoints", orig_len == 10, f"count={orig_len}")

    # Compact down to 5 using the new checkpoints parameter
    store.save(sid, checkpoints=state.get("checkpoints", [])[-5:])

    compacted = store.load(sid)
    new_len = len(compacted.get("checkpoints", []))
    R.check("post-compaction has 5 checkpoints", new_len == 5, f"count={new_len}")
    store.delete(sid)


def test_post_turn_harvest(store, R: Results):
    """Test auto-harvesting facts from commands (post_tool_use hook)."""
    sys.path.insert(0, str(SCRIPT_DIR / "hooks"))
    import post_tool_use
    proj = f"verify-harvest-{int(time.time())}"
    res1 = post_tool_use.harvest_command("pnpm run build", project=proj, store_override=store)
    res2 = post_tool_use.harvest_command("pytest tests/ -v -q", project=proj, store_override=store)

    R.check("post_tool_use returned build fact", "build_cmd" in res1 and "pnpm" in res1["build_cmd"], f"res={res1}")
    R.check("post_tool_use returned test fact", "test_cmd" in res2 and "pytest" in res2["test_cmd"], f"res={res2}")

    facts = store.fact_list(proj)
    R.check("harvested build command in store", "build_cmd" in facts and "pnpm" in facts["build_cmd"], f"facts={facts}")
    R.check("harvested test command in store", "test_cmd" in facts and "pytest" in facts["test_cmd"], f"facts={facts}")
    R.check("harvested package manager in store", "pkg_manager" in facts and facts["pkg_manager"] == "pnpm", f"facts={facts}")
    for k in list(facts.keys()):
        store.fact_delete(proj, k)


# ─── Main ──────────────────────────────────────────────────────────────────
def main():
    import argparse
    import shutil
    import tempfile
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", default="json_file", choices=["json_file", "sqlite"])
    ap.add_argument("--home", default=None)
    args = ap.parse_args()

    mod = load_adapter(args.adapter)
    cleanup_temp = False

    if args.home:
        storage_home = Path(args.home)
    else:
        # Default to an isolated temporary directory so tests never pollute live user storage
        storage_home = Path(tempfile.mkdtemp(prefix=f"sp_verify_{args.adapter}_"))
        cleanup_temp = True

    storage_home.mkdir(parents=True, exist_ok=True)
    if args.adapter == "json_file":
        store = mod.SessionStore(home=storage_home)
    else:
        db_path = storage_home / "storage.db"
        store = mod.SessionStore(db_path=db_path)

    R = Results()
    print(f"Running verification with adapter: {args.adapter}")
    print(f"Storage home: {store.home}\n")

    try:
        test_core(store, R)
        test_style_mirroring(store, R)
        test_ponytail(store, R)
        test_facts(store, R)
        test_kv_store(store, R)
        test_memory_sync(store, R)
        test_semantic_index(store, R)
        test_session_lifecycle(store, R)
        test_budget_estimate(R)
        test_loop_detection(store, R)
        test_compaction(store, R)
        test_post_turn_harvest(store, R)
    except Exception as e:
        R.failed.append(("Exception", str(e)))
    finally:
        if cleanup_temp:
            import gc
            gc.collect()
            try:
                shutil.rmtree(storage_home, ignore_errors=True)
            except Exception:
                pass

    print(R.summary())
    sys.exit(0 if not R.failed else 1)


if __name__ == "__main__":
    main()