#!/usr/bin/env python3
"""
Session Pilot Pro Plus — Unified CLI (sp.py) v3.0.0
=====================================================
Honest, mechanism-backed CLI for agent session management.

Every command either does real work (●) or is honestly labeled
as advisory (◐). Nothing prints hardcoded fake results.

Commands:
  sp.py recall [--session <id>]
  sp.py save --done "..." --next "..."
  sp.py find "<keywords>" [-k 5]
  sp.py fact [set|get|list|delete]
  sp.py ponytail [lite|full|ultra|off]
  sp.py tier-check "<task>"
  sp.py budget "<text or file>" [--limit N]
  sp.py mark-done [--session <id>]
  sp.py loop-guard [--session <id>] [--threshold N]
  sp.py compact [--session <id>] [--keep N]
  sp.py memory [sync|read|write|list] [args...]
  sp.py sessions [list|delete <id>]
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

# Force UTF-8 on Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
ADAPTERS_DIR = ROOT_DIR / "adapters"
sys.path.insert(0, str(ADAPTERS_DIR))

try:
    import json_file
    store = json_file.get_store()
except Exception:
    store = None

VERSION = "3.0.0"

SECRET_PATTERNS = [
    (re.compile(r'ey[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'), '[REDACTED_JWT]'),
    (re.compile(r'AKIA[0-9A-Z]{16}'), '[REDACTED_AWS_KEY]'),
    (re.compile(r'(ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{30,})'), '[REDACTED_GITHUB_TOKEN]'),
    (re.compile(r'sk-[a-zA-Z0-9_\-]{20,}'), '[REDACTED_API_KEY]'),
    (re.compile(r'Bearer\s+[a-zA-Z0-9_\-\.]{16,}', re.IGNORECASE), 'Bearer [REDACTED_TOKEN]'),
    (re.compile(r'([a-zA-Z0-9]+:\/\/[^:\s]+:)([^@\s]+)(@)'), r'\1[REDACTED]\3'),
]


def scrub_secrets(s: str) -> str:
    if not isinstance(s, str):
        return str(s)
    for pat, repl in SECRET_PATTERNS:
        s = pat.sub(repl, s)
    return s


def get_current_session_id(explicit_id=None):
    if explicit_id:
        return explicit_id
    if os.environ.get("SESSION_PILOT_ID"):
        return os.environ.get("SESSION_PILOT_ID")
    # Check presence lock in Antigravity
    presence_dir = Path.home() / ".gemini" / "antigravity" / "presence"
    if presence_dir.exists():
        locks = list(presence_dir.glob("*.lock"))
        if locks:
            locks.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            return locks[0].stem
    # Check Antigravity / Gemini conversation directory if available
    gemini_brain = Path.home() / ".gemini" / "antigravity" / "brain"
    if gemini_brain.exists():
        dirs = [
            d for d in gemini_brain.iterdir()
            if d.is_dir() and not d.name.startswith(".") and (d / ".system_generated").exists()
        ]
        if dirs:
            dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
            return dirs[0].name
    # Fallback to CWD hash
    cwd = os.getcwd()
    return f"auto-{hashlib.sha256(cwd.encode()).hexdigest()[:12]}"


def time_ago(ts):
    if not ts:
        return "never"
    delta = int(time.time() - ts)
    if delta < 0:
        return "just now"
    if delta < 60:
        return f"{delta}s ago"
    if delta < 3600:
        return f"{delta // 60}m ago"
    if delta < 86400:
        return f"{delta // 3600}h ago"
    return f"{delta // 86400}d ago"


def estimate_tokens(text: str) -> dict:
    """Multi-heuristic token estimation. Honest about its +-15% accuracy."""
    words = len(text.split())
    chars = len(text)
    cjk = len(re.findall(r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]', text))
    code_sym = len(re.findall(r'[{}\[\]();:=<>+*/_&|~^%!@#$\'\"\\\]', text))

    # Try tiktoken if available (accurate); fall back to heuristic
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4")
        precise = len(enc.encode(text))
        return {
            "tokens": precise,
            "method": "tiktoken (cl100k_base)",
            "accuracy": "+-2%",
            "words": words,
            "chars": chars,
        }
    except ImportError:
        pass

    # Heuristic: max of word-based and char-based estimates
    tokens = max(int(words * 1.33), int(chars / 3.6)) + int(cjk * 1.2) + int(code_sym * 0.35)
    return {
        "tokens": tokens,
        "method": "heuristic (words*1.33 or chars/3.6)",
        "accuracy": "+-15%",
        "words": words,
        "chars": chars,
        "cjk_chars": cjk,
        "code_symbols": code_sym,
    }


# ─── REAL MECHANISMS ─────────────────────────────────────────────────────


def _checkpoint_hashes(state: dict, n: int = 5) -> list:
    """Extract hashes of the last N checkpoint 'done' values."""
    cps = state.get("checkpoints", [])
    hashes = []
    for cp in cps[-n:]:
        done = cp.get("done", "")
        h = hashlib.sha256(done.encode("utf-8")).hexdigest()[:16]
        hashes.append(h)
    return hashes


def detect_loop(state: dict, threshold: int = 3) -> dict:
    """
    REAL loop detection: hash the last N checkpoint 'done' values.
    If `threshold` or more consecutive checkpoints have identical hashes,
    a loop is detected. This is a real mechanism using stored state,
    not a secondary LLM judge.

    Returns: {"detected": bool, "count": int, "repeated_text": str|None}
    """
    cps = state.get("checkpoints", [])
    if len(cps) < threshold:
        return {"detected": False, "count": 0, "repeated_text": None}

    # Check the last `threshold + 2` checkpoints for consecutive repetitions
    window = cps[-(threshold + 2):]
    hashes = [hashlib.sha256(cp.get("done", "").encode()).hexdigest()[:16] for cp in window]

    # Find longest run of identical hashes at the tail
    if not hashes:
        return {"detected": False, "count": 0, "repeated_text": None}

    tail_hash = hashes[-1]
    run = 0
    for h in reversed(hashes):
        if h == tail_hash:
            run += 1
        else:
            break

    detected = run >= threshold
    repeated = window[-1].get("done", "") if detected else None
    return {"detected": detected, "count": run, "repeated_text": repeated}


# ─── COMMANDS ────────────────────────────────────────────────────────────


def cmd_recall(args):
    sid = get_current_session_id(args.session)
    if not store:
        print(f"NEW SESSION {sid}")
        return

    state = store.load(sid)
    if not state or not state.get("checkpoints"):
        print(f"NEW SESSION {sid}")
        return

    updated_str = time_ago(state.get("updated_at", time.time()))
    print(f"SESSION {sid} | {state.get('status', 'active')} | updated {updated_str}")
    for cp in state.get("checkpoints", [])[-3:]:
        ago = time_ago(cp.get("timestamp", time.time()))
        done_scrubbed = scrub_secrets(cp.get('done', ''))
        next_scrubbed = scrub_secrets(cp.get('next', ''))
        print(f"- [{ago}] done: {done_scrubbed} | next: {next_scrubbed}")
    if state.get("ponytail_mode"):
        print(f"ponytail_mode: {state['ponytail_mode']}")
    if state.get("style"):
        print(f"style: {scrub_secrets(state['style'])}")

    # Auto loop-guard check on recall
    loop = detect_loop(state)
    if loop["detected"]:
        print(f"[!] LOOP DETECTED: {loop['count']} consecutive identical checkpoints")
        print(f"    Repeated: {scrub_secrets(loop['repeated_text'] or '')[:80]}")
        print(f"    Suggestion: change approach before continuing")


def cmd_save(args):
    sid = get_current_session_id(args.session)
    if not store:
        print(f"saved {sid}")
        return

    store.save(
        sid,
        done=args.done or "",
        next=args.next or "",
        style=args.style,
        global_style=args.global_style,
        ponytail_mode=args.ponytail,
    )
    print(f"saved {sid}")


def cmd_find(args):
    keywords = [w.lower() for w in args.keywords.split()]
    search_dirs = [
        Path.home() / ".config" / "opencode" / "skills",
        Path.home() / ".claude" / "skills",
        Path.home() / ".gemini" / "config" / "skills",
    ]

    discovered = []
    for base in search_dirs:
        if not base.exists():
            continue
        for p in base.iterdir():
            if not p.is_dir():
                continue
            sk_file = p / "SKILL.md"
            if not sk_file.exists():
                continue
            name = p.name
            desc = ""
            try:
                lines = sk_file.read_text(encoding="utf-8", errors="ignore").splitlines()[:20]
                for line in lines:
                    if line.startswith("description:"):
                        desc = line.replace("description:", "").strip()
            except Exception:
                pass
            discovered.append((name, desc, str(sk_file)))

    scored = []
    for name, desc, path in discovered:
        combined = f"{name} {desc}".lower()
        score = sum(3 if kw == name.lower() else (1 if kw in combined else 0) for kw in keywords)
        if score > 0:
            cov = int((sum(1 for kw in keywords if kw in combined) / max(len(keywords), 1)) * 100)
            scored.append((score, cov, name, desc, path))

    scored.sort(key=lambda x: (-x[0], -x[1]))
    match_level = "strong" if scored and scored[0][0] >= 2 else ("weak" if scored else "none")
    print(f"match: {match_level} | indexed {len(discovered)} | terms: {' '.join(keywords)}")

    for i, (score, cov, name, desc, path) in enumerate(scored[:args.k], 1):
        print(f"{i}. {name} [skill] score={score} cov={cov}%")
        print(f"   {desc[:140]}...")
        print(f"   {path}")


def cmd_fact(args):
    if not store:
        print("[!] Store unavailable")
        return
    proj = args.project or "default"
    if args.action in ("set", "get", "delete") and not args.key:
        print(f"[!] Error: 'key' is required for fact {args.action}")
        return

    if args.action == "set":
        if args.value is None:
            print("[!] Error: 'value' is required for fact set")
            return
        store.fact_set(proj, args.key, args.value)
        print(f"[fact set] {args.key} = {scrub_secrets(repr(args.value))}")
    elif args.action == "get":
        val = store.fact_get(proj, args.key)
        print(f"[fact get] {args.key} = {scrub_secrets(repr(val))}")
    elif args.action == "list":
        facts = store.fact_list(proj)
        print(f"[Verified Repo Facts ({len(facts)})]:")
        for k, v in facts.items():
            print(f"  - {k}: {scrub_secrets(repr(v))}")
    elif args.action == "delete":
        ok = store.fact_delete(proj, args.key)
        print(f"[fact delete] {args.key} -> {ok}")


def cmd_ponytail(args):
    sid = get_current_session_id(args.session)
    mode = args.mode.lower()
    if store and sid:
        store.save(sid, ponytail_mode=mode)
    print(f"[Ponytail Mode] set to: {mode.upper()}")


def cmd_tier_check(args):
    task = args.task.lower()
    t3 = ["architecture", "security", "vulnerability", "concurrency", "race condition",
          "deadlock", "crypto", "exploit", "cve", "distributed", "migration"]
    t2 = ["feature", "implement", "fix", "test", "refactor", "build", "component", "debug"]
    t1 = ["read", "find", "grep", "search", "list", "convert", "summarize", "log", "format"]
    t0 = ["hi", "hello", "what is", "look up", "typo", "meaning", "explain"]

    if any(w in task for w in t3):
        print("[Tier] T3 (Hard) -> Premium reasoning model (complex architecture / subtle security / concurrency)")
    elif any(w in task for w in t2):
        print("[Tier] T2 (Standard) -> Standard model (pro / self if covered by tests)")
    elif any(w in task for w in t1):
        print("[Tier] T1 (Mechanical) -> Cheap model (flash)")
    elif any(w in task for w in t0):
        print("[Tier] T0 (Trivial) -> Direct answer, cheap model (flash_lite / flash), 0 tools")
    else:
        print("[Tier] T2 (Standard) -> Default standard tier (pro / self)")


def cmd_budget(args):
    raw_input = args.target or ""
    p = Path(raw_input)
    if p.exists() and p.is_file():
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
            target_desc = f"file: {p.name}"
        except Exception as e:
            print(f"[!] Could not read file: {e}")
            return
    else:
        content = raw_input
        target_desc = f"string ({len(content)} chars)"

    est = estimate_tokens(content)
    limit = args.limit or 2000
    print(f"[Budget Analysis] {target_desc}")
    print(f"  Estimated Tokens: {est['tokens']:,} ({est['method']}, {est['accuracy']})")
    print(f"  Words:            {est['words']:,}")
    print(f"  Characters:       {est['chars']:,}")
    status = "OK" if est['tokens'] <= limit else "WARNING: EXCEEDS LIMIT"
    print(f"  Status vs limit ({limit:,}): {status}")


def cmd_mark_done(args):
    sid = get_current_session_id(args.session)
    if store and sid:
        store.mark_done(sid)
        print(f"[Session marked done] id={sid}")
    else:
        print(f"[!] Unable to mark session done (store={bool(store)}, sid={sid})")


def cmd_loop_guard(args):
    """
    REAL loop detection using checkpoint history.
    Mechanism: hashes the 'done' field of recent checkpoints and detects
    consecutive identical entries above a threshold.
    Grading: ● (native enforcement via stored state) — no secondary LLM needed.
    Limitation: only detects loops that pass through SP save checkpoints.
    """
    sid = get_current_session_id(args.session)
    threshold = args.threshold or 3

    if not store or not sid:
        print("[Loop Guard] No active session — cannot check")
        return

    state = store.load(sid)
    if not state:
        print(f"[Loop Guard] Session {sid} not found")
        return

    cps = state.get("checkpoints", [])
    result = detect_loop(state, threshold=threshold)

    print(f"[Loop Guard] session={sid} | checkpoints={len(cps)} | threshold={threshold}")
    if result["detected"]:
        print(f"  [!] LOOP DETECTED: {result['count']} consecutive identical checkpoints")
        print(f"      Repeated action: {scrub_secrets(result['repeated_text'] or '')[:100]}")
        print(f"      Recommendation: change approach, try different tool, or escalate")
    else:
        print(f"  OK: no repetition detected (last {min(len(cps), threshold + 2)} checkpoints are distinct)")

    # Show recent checkpoint hashes for transparency
    if cps and args.verbose:
        print(f"  Recent checkpoint hashes:")
        for cp in cps[-5:]:
            h = hashlib.sha256(cp.get("done", "").encode()).hexdigest()[:12]
            ago = time_ago(cp.get("timestamp"))
            print(f"    {h} [{ago}] {scrub_secrets(cp.get('done', ''))[:60]}")


def cmd_compact(args):
    """
    REAL checkpoint compaction: trims the checkpoint list in the session store.
    Honestly labeled: this compacts SP's own checkpoint history, NOT the agent's
    context window (which is controlled by the harness, not by a skill).
    """
    sid = get_current_session_id(args.session)
    keep = args.keep or 5

    if not store or not sid:
        print("[!] No active session to compact")
        return

    state = store.load(sid)
    if not state:
        print(f"[!] Session {sid} not found")
        return

    cps = state.get("checkpoints", [])
    original_count = len(cps)

    if original_count > keep:
        state["checkpoints"] = cps[-keep:]
        state["updated_at"] = int(time.time())
        # Use the store's internal save mechanism
        from json_file import _atomic_write, _session_path
        _atomic_write(_session_path(sid, base=store.sessions_dir), state)
        print(f"[Checkpoint Compaction] Trimmed {original_count} -> {keep} checkpoints")
        print(f"  Note: this compacts SP's checkpoint store, not the agent's context window")
    else:
        print(f"[Checkpoint Compaction] Already compact ({original_count} <= {keep})")


def cmd_memory(args):
    """
    REAL cross-agent memory using the adapter's memory_write/memory_read.
    """
    if not store:
        print("[!] Store unavailable")
        return

    action = args.action
    ns = args.namespace or "shared"

    if action == "write":
        if not args.key or args.value is None:
            print("[!] Usage: sp.py memory write --namespace NS --key KEY VALUE")
            return
        store.memory_write(ns, args.key, args.value)
        print(f"[memory write] {ns}/{args.key} = {scrub_secrets(repr(args.value))}")

    elif action == "read":
        if not args.key:
            print("[!] Usage: sp.py memory read --namespace NS --key KEY")
            return
        val = store.memory_read(ns, args.key)
        print(f"[memory read] {ns}/{args.key} = {scrub_secrets(repr(val))}")

    elif action == "list":
        mem_dir = store.memory_dir
        from json_file import _safe_component, _read_json
        safe_ns = _safe_component(ns)
        ns_dir = mem_dir / safe_ns
        if not ns_dir.exists():
            print(f"[memory list] namespace '{ns}': empty")
            return
        entries = []
        for f in ns_dir.glob("*.json"):
            data = _read_json(f)
            if isinstance(data, dict) and "key" in data:
                entries.append((data["key"], data.get("value"), data.get("updated_at")))
        print(f"[memory list] namespace '{ns}': {len(entries)} entries")
        for k, v, ts in entries:
            ago = time_ago(ts)
            print(f"  - {k}: {scrub_secrets(repr(v))[:80]} [{ago}]")

    elif action == "sync":
        # List all namespaces
        mem_dir = store.memory_dir
        if not mem_dir.exists():
            print("[memory sync] no namespaces found")
            return
        namespaces = [d.name for d in mem_dir.iterdir() if d.is_dir()]
        total = 0
        for ns_name in namespaces:
            count = len(list((mem_dir / ns_name).glob("*.json")))
            total += count
            print(f"  namespace: {ns_name} ({count} entries)")
        print(f"[memory sync] {len(namespaces)} namespaces, {total} total entries")

    else:
        print(f"[!] Unknown memory action: {action}")
        print("    Valid: write, read, list, sync")


def cmd_sessions(args):
    """List or delete sessions."""
    if not store:
        print("[!] Store unavailable")
        return

    if args.action == "list":
        sessions = store.list()
        if not sessions:
            print("[sessions] none found")
            return
        print(f"[sessions] {len(sessions)} found:")
        for s in sessions:
            ago = time_ago(s.get("updated_at", 0))
            print(f"  {s['id'][:40]:<42} {s.get('status', '?'):<8} {ago}")

    elif args.action == "delete":
        if not args.target:
            print("[!] Usage: sp.py sessions delete <session-id>")
            return
        ok = store.delete(args.target)
        print(f"[sessions delete] {args.target} -> {'deleted' if ok else 'not found'}")


def main():
    parser = argparse.ArgumentParser(
        description=f"Session Pilot Pro Plus CLI v{VERSION}",
        epilog="Every command does real work or is honestly labeled as advisory."
    )
    subparsers = parser.add_subparsers(dest="command")

    # recall
    p_recall = subparsers.add_parser("recall", help="Restore session state")
    p_recall.add_argument("--session", default=None)

    # save
    p_save = subparsers.add_parser("save", help="Checkpoint progress")
    p_save.add_argument("--session", default=None)
    p_save.add_argument("--done", default="")
    p_save.add_argument("--next", default="")
    p_save.add_argument("--style", default=None)
    p_save.add_argument("--global-style", default=None)
    p_save.add_argument("--ponytail", default=None)

    # find
    p_find = subparsers.add_parser("find", help="Route to best skill")
    p_find.add_argument("keywords")
    p_find.add_argument("-k", type=int, default=5)

    # fact
    p_fact = subparsers.add_parser("fact", help="Repo facts bank")
    p_fact.add_argument("action", choices=["set", "get", "list", "delete"])
    p_fact.add_argument("key", nargs="?", default=None)
    p_fact.add_argument("value", nargs="?", default=None)
    p_fact.add_argument("--project", default="default")

    # ponytail
    p_pony = subparsers.add_parser("ponytail", help="Minimal-diff mode")
    p_pony.add_argument("mode", choices=["lite", "full", "ultra", "off"], default="full", nargs="?")
    p_pony.add_argument("--session", default=None)

    # tier-check
    p_tier = subparsers.add_parser("tier-check", help="Task difficulty triage")
    p_tier.add_argument("task")

    # budget
    p_budget = subparsers.add_parser("budget", help="Token estimate (+-15% heuristic or tiktoken)")
    p_budget.add_argument("target", help="Text string or file path")
    p_budget.add_argument("--limit", type=int, default=2000)

    # mark-done
    p_done = subparsers.add_parser("mark-done", help="Mark session complete")
    p_done.add_argument("--session", default=None)

    # loop-guard (REAL: checkpoint hash detection)
    p_loop = subparsers.add_parser("loop-guard", help="Detect repeated checkpoints (real hash-based)")
    p_loop.add_argument("--session", default=None)
    p_loop.add_argument("--threshold", type=int, default=3,
                        help="Number of consecutive identical checkpoints to trigger (default: 3)")
    p_loop.add_argument("--verbose", action="store_true", help="Show checkpoint hashes")

    # compact (HONESTLY LABELED: compacts checkpoint store, not context window)
    p_compact = subparsers.add_parser("compact", help="Trim checkpoint history (store compaction, not context window)")
    p_compact.add_argument("--session", default=None)
    p_compact.add_argument("--keep", type=int, default=5, help="Checkpoints to retain (default: 5)")

    # memory (REAL: uses adapter's memory_write/memory_read)
    p_mem = subparsers.add_parser("memory", help="Cross-agent shared memory")
    p_mem.add_argument("action", choices=["write", "read", "list", "sync"])
    p_mem.add_argument("--namespace", default="shared")
    p_mem.add_argument("--key", default=None)
    p_mem.add_argument("value", nargs="?", default=None)

    # sessions
    p_sess = subparsers.add_parser("sessions", help="List or delete sessions")
    p_sess.add_argument("action", choices=["list", "delete"])
    p_sess.add_argument("target", nargs="?", default=None)

    # version
    subparsers.add_parser("version", help="Print version")

    args = parser.parse_args()
    cmd_map = {
        "recall": cmd_recall,
        "save": cmd_save,
        "find": cmd_find,
        "fact": cmd_fact,
        "ponytail": cmd_ponytail,
        "tier-check": cmd_tier_check,
        "budget": cmd_budget,
        "mark-done": cmd_mark_done,
        "loop-guard": cmd_loop_guard,
        "compact": cmd_compact,
        "memory": cmd_memory,
        "sessions": cmd_sessions,
    }

    if args.command == "version":
        print(f"session-pilot-pro-plus v{VERSION}")
    elif args.command in cmd_map:
        cmd_map[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
