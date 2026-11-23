#!/usr/bin/env python3
"""
Session Pilot Pro Plus — Interactive Demo REPL v3.0.0
======================================================
A minimal prompt-driven shell to exercise every SP command
without wiring it into an LLM harness first. Run with:

    python scripts/repl.py [--adapter json_file|sqlite] [--home ~/.session-pilot-pro-plus]

Every command invokes real adapter code — nothing prints fake results.
"""

import argparse
import hashlib
import re
import sys
import time
from pathlib import Path

# Windows console: force UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

SKILL_ROOT = Path(__file__).resolve().parent.parent
ADAPTER_DIR = SKILL_ROOT / "adapters"


def load_adapter(name: str):
    module_path = ADAPTER_DIR / f"{name}.py"
    if not module_path.exists():
        print(f"[!] Adapter '{name}' not found at {module_path}")
        sys.exit(1)
    import importlib.util
    spec = importlib.util.spec_from_file_location(f"sp_adapter_{name}", module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.get_store()


def banner():
    print("""
+--------------------------------------------------------------+
|       Session Pilot Pro Plus — Interactive REPL v3.0.0        |
|   Honest agent memory & discipline skill with real adapters   |
+--------------------------------------------------------------+

Commands (type 'help' for full list):
  SP recall [SESSION_ID]          Load or create a session
  SP save --done X --next Y       Checkpoint progress
  SP ponytail [lite|full|ultra]   Toggle minimal-diff mode
  SP fact set KEY VALUE           Record durable repo fact
  SP fact list                    List verified repository facts
  SP tier-check "task"            Task difficulty triage
  SP loop-guard                   Check for repeated checkpoints
  SP compact [--keep N]           Trim checkpoint store
  SP memory [sync|write|read]     Cross-agent shared memory
  SP budget --limit N             Token estimate (+-15% heuristic)
  SP find "keywords"              Route to best skill
  SP mark-done                    Mark current session complete
  SP sessions list                List all sessions
  SP exit                         Quit
""")


COMMANDS = {
    "recall":     "--session ID     Load or create a session",
    "save":       "--done ... --next ...  Checkpoint for later resume",
    "ponytail":   "[lite|full|ultra|off]  Minimal-diff Lazy Senior Dev mode",
    "fact":       "set/get/list/delete    Repo facts bank",
    "tier-check": "\"task\"               Task difficulty triage (T0..T3)",
    "loop-guard": "                       Check for checkpoint repetition loops",
    "compact":    "[--keep N]             Trim checkpoint store (not context window)",
    "mark-done":  "                       Mark session complete",
    "list":       "                       List all sessions",
    "delete":     "SESSION_ID             Remove a session",
    "budget":     "--limit N              Estimate token count (+-15%)",
    "find":       "\"keywords\"             Route to best installed skill",
    "list-skills":"                       Show discoverable skills",
    "persist":    "set/get KEY [VALUE]    Project key/value store",
    "memory":     "sync/write/read/list   Cross-agent shared memory",
    "exit":       "                       Quit REPL",
}


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


def cmd_recall(store, args):
    sid = args.strip() if args.strip() else f"demo-{int(time.time())}"
    state = store.get_or_create(sid, title=sid)
    print(f"\n[Session loaded] id={state['id']}  status={state['status']}")
    print(f"  Goal: {state.get('goal') or '(none)'}")
    cp = state.get("checkpoints", [])
    print(f"  Checkpoints: {len(cp)}")
    for c in cp[-3:]:
        ago = time_ago(c.get("timestamp"))
        print(f"    done: {c['done']!r}  -> next: {c['next']!r}  [{ago}]")
    style = state.get("style") or state.get("global_style")
    if style:
        print(f"  Style: {style!r}")

    # Auto loop check
    from sp import detect_loop
    loop = detect_loop(state)
    if loop["detected"]:
        print(f"  [!] LOOP WARNING: {loop['count']} consecutive identical checkpoints")

    return sid


def cmd_save(store, sid, args):
    m_done = re.search(r'--done(?:\s+|=)(?:"([^"]*)"|\'([^\']*)\'|(\S+))', args)
    m_next = re.search(r'--next(?:\s+|=)(?:"([^"]*)"|\'([^\']*)\'|(\S+))', args)
    m_style = re.search(r'--style(?:\s+|=)(?:"([^"]*)"|\'([^\']*)\'|(\S+))', args)

    done = (m_done.group(1) or m_done.group(2) or m_done.group(3) or "") if m_done else ""
    next_step = (m_next.group(1) or m_next.group(2) or m_next.group(3) or "") if m_next else ""
    style = (m_style.group(1) or m_style.group(2) or m_style.group(3) or None) if m_style else None

    state = store.save(sid, done=done, next=next_step, style=style)
    print(f"[Checkpoint saved]  done={done!r}  next={next_step!r}")
    print(f"  Checkpoints count: {len(state.get('checkpoints', []))}")


def cmd_mark_done(store, sid):
    state = store.mark_done(sid)
    print(f"[Session marked done]  id={sid}  status={state.get('status', 'done')}")


def cmd_list(store, _args):
    sessions = store.list()
    if not sessions:
        print("[No sessions found]")
        return
    print(f"\n{'ID':<40} {'Status':<10} {'Updated':>14}")
    print("-" * 66)
    for s in sessions:
        ago = time_ago(s.get("updated_at", 0))
        sid_display = s['id'][:38]
        print(f"{sid_display:<40} {s['status']:<10} {ago:>14}")


def cmd_delete(store, sid):
    ok = store.delete(sid)
    print(f"[Deleted] {sid} -> {ok}")


def cmd_budget(_store, args):
    m = re.search(r"--limit\s+(\d+)", args)
    limit = int(m.group(1)) if m else 500
    text = re.sub(r'--limit\s+\d+', '', args).strip()
    if not text:
        text = "sample text for estimation"

    # Real token estimation
    words = len(text.split())
    chars = len(text)
    tokens = max(int(words * 1.33), int(chars / 3.6))

    print(f"[Budget check]  limit={limit}  est_tokens={tokens} (+-15% heuristic)")
    print(f"  Words: {words}  Chars: {chars}")
    if tokens > limit:
        print(f"  [!] EXCEEDS LIMIT — trim context or reduce loaded helpers")
    else:
        print(f"  OK: within budget ({tokens}/{limit} tokens)")


def cmd_find(_store, args):
    """Real keyword routing against installed skills on disk."""
    search_dirs = [
        Path.home() / ".config" / "opencode" / "skills",
        Path.home() / ".claude" / "skills",
        Path.home() / ".gemini" / "config" / "skills",
    ]
    keywords = [w.lower() for w in args.split()]
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
            scored.append((score, name, desc))
    scored.sort(key=lambda x: -x[0])

    match_level = "strong" if scored and scored[0][0] >= 2 else ("weak" if scored else "none")
    print(f"[SP find '{args}']  match: {match_level} | indexed {len(discovered)}")
    for score, name, desc in scored[:5]:
        print(f"  #{score}: {name:<35} {desc[:60]}")


def cmd_list_skills(store, _args):
    search_dirs = [
        Path.home() / ".config" / "opencode" / "skills",
        Path.home() / ".claude" / "skills",
        Path.home() / ".gemini" / "config" / "skills",
    ]
    total = 0
    for base in search_dirs:
        if not base.exists():
            continue
        skills = [p for p in base.iterdir() if p.is_dir() and (p / "SKILL.md").exists()]
        if skills:
            print(f"\n  {base}:")
            for p in sorted(skills):
                print(f"    {p.name}")
                total += 1
    print(f"\n  Total: {total} skills discovered")


def cmd_persist(store, args):
    parts = args.strip().split(maxsplit=2)
    subcmd = parts[0] if parts else ""
    if subcmd == "set" and len(parts) >= 3:
        key, val = parts[1], parts[2]
        store.kv_set("__demo__", key, val)
        print(f"[persist set] {key}={val!r}")
    elif subcmd == "get" and len(parts) >= 2:
        key = parts[1]
        val = store.kv_get("__demo__", key)
        print(f"[persist get] {key}={val!r}")
    else:
        print("Usage: SP persist set KEY VALUE  OR  SP persist get KEY")


def cmd_ponytail(store, sid, args):
    mode = args.strip().lower() or "full"
    if mode not in ("lite", "full", "ultra", "off"):
        print("[!] Valid modes: lite, full, ultra, off")
        return
    if sid:
        store.save(sid, ponytail_mode=mode)
    print(f"[Ponytail Mode] set to: {mode.upper()}")
    descriptions = {
        "lite": "Build what was asked. Name smaller option in 1 line.",
        "full": "Smallest complete change. Zero unrequested bloat. Transparency note required.",
        "ultra": "Question the request: actively push back on unneeded complexity.",
        "off": "Normal agent behavior restored.",
    }
    print(f"  {descriptions.get(mode, '')}")


def cmd_fact(store, args):
    parts = args.strip().split(maxsplit=2)
    subcmd = parts[0] if parts else ""
    if subcmd == "set" and len(parts) >= 3:
        key, val = parts[1], parts[2]
        store.fact_set("__demo__", key, val)
        print(f"[Fact Set] {key} = {val!r}")
    elif subcmd == "get" and len(parts) >= 2:
        key = parts[1]
        val = store.fact_get("__demo__", key)
        print(f"[Fact Get] {key} = {val!r}")
    elif subcmd == "list":
        facts = store.fact_list("__demo__")
        if not facts:
            print("[No facts recorded for project]")
        else:
            print(f"[Verified Repo Facts ({len(facts)})]:")
            for k, v in facts.items():
                print(f"  - {k}: {v}")
    elif subcmd == "delete" and len(parts) >= 2:
        key = parts[1]
        ok = store.fact_delete("__demo__", key)
        print(f"[Fact Delete] {key} -> {ok}")
    else:
        print("Usage: SP fact set KEY VALUE  |  SP fact get KEY  |  SP fact list  |  SP fact delete KEY")


def cmd_tier_check(args):
    task = args.strip() or "general task"
    t_lower = task.lower()
    t3 = ["architecture", "security", "vulnerability", "concurrency", "race condition",
          "deadlock", "crypto", "exploit", "cve", "distributed", "migration"]
    t2 = ["feature", "implement", "fix", "test", "refactor", "build", "component", "debug"]
    t1 = ["read", "find", "search", "list", "format", "convert", "grep"]
    t0 = ["hi", "hello", "what is", "explain", "look up", "typo"]

    if any(w in t_lower for w in t3):
        tier, target = "T3 (Hard)", "Flagship reasoning model"
    elif any(w in t_lower for w in t2):
        tier, target = "T2 (Standard)", "Balanced model (pro)"
    elif any(w in t_lower for w in t1):
        tier, target = "T1 (Mechanical)", "flash model"
    elif any(w in t_lower for w in t0):
        tier, target = "T0 (Trivial)", "Direct answer, flash_lite"
    else:
        tier, target = "T2 (Standard)", "Balanced model (pro)"
    print(f"[Tier Triage] task: '{task}'")
    print(f"  Level:  {tier}")
    print(f"  Action: {target}")


def cmd_loop_guard(store, sid, args):
    """REAL loop detection using checkpoint hashes."""
    if not sid:
        print("[!] No active session. Run SP recall first.")
        return
    state = store.load(sid)
    if not state:
        print(f"[!] Session {sid} not found")
        return

    sys.path.insert(0, str(SKILL_ROOT / "scripts"))
    from sp import detect_loop
    result = detect_loop(state, threshold=3)
    cps = state.get("checkpoints", [])

    print(f"[Loop Guard] session={sid} | checkpoints={len(cps)} | threshold=3")
    if result["detected"]:
        print(f"  [!] LOOP DETECTED: {result['count']} consecutive identical checkpoints")
        print(f"      Repeated: {result['repeated_text'][:80] if result['repeated_text'] else '?'}")
        print(f"      Recommendation: change approach or escalate")
    else:
        print(f"  OK: no repetition detected")


def cmd_compact(store, sid, args):
    """REAL checkpoint compaction."""
    if not sid:
        print("[!] No active session.")
        return
    m = re.search(r'--keep\s+(\d+)', args)
    keep = int(m.group(1)) if m else 5

    state = store.load(sid)
    if not state:
        print(f"[!] Session {sid} not found")
        return
    cps = state.get("checkpoints", [])
    orig = len(cps)
    if orig > keep:
        state["checkpoints"] = cps[-keep:]
        state["updated_at"] = int(time.time())
        # Save using the store
        store.save(sid)  # re-save with trimmed checkpoints
        print(f"[Checkpoint Compaction] Trimmed {orig} -> {keep}")
        print(f"  Note: compacts SP's checkpoint store, not agent context window")
    else:
        print(f"[Checkpoint Compaction] Already compact ({orig} <= {keep})")


def cmd_memory(store, args):
    """REAL cross-agent memory via adapter."""
    parts = args.strip().split(maxsplit=3)
    action = parts[0] if parts else ""

    if action == "sync":
        mem_dir = store.memory_dir
        if not mem_dir.exists():
            print("[memory sync] no namespaces found")
            return
        namespaces = [d.name for d in mem_dir.iterdir() if d.is_dir()]
        total = 0
        for ns in namespaces:
            count = len(list((mem_dir / ns).glob("*.json")))
            total += count
            print(f"  namespace: {ns} ({count} entries)")
        print(f"[memory sync] {len(namespaces)} namespaces, {total} total entries")

    elif action == "write" and len(parts) >= 4:
        ns, key, val = parts[1], parts[2], parts[3]
        store.memory_write(ns, key, val)
        print(f"[memory write] {ns}/{key} = {val!r}")

    elif action == "read" and len(parts) >= 3:
        ns, key = parts[1], parts[2]
        val = store.memory_read(ns, key)
        print(f"[memory read] {ns}/{key} = {val!r}")

    elif action == "list" and len(parts) >= 2:
        ns = parts[1]
        from json_file import _safe_component, _read_json
        safe_ns = _safe_component(ns)
        ns_dir = store.memory_dir / safe_ns
        if not ns_dir.exists():
            print(f"[memory list] namespace '{ns}': empty")
            return
        for f in ns_dir.glob("*.json"):
            data = _read_json(f)
            if isinstance(data, dict) and "key" in data:
                print(f"  {data['key']}: {data.get('value')!r}")

    else:
        print("Usage: SP memory sync | SP memory write NS KEY VAL | SP memory read NS KEY | SP memory list NS")


def main():
    parser = argparse.ArgumentParser(description="Session Pilot Pro Plus — REPL v3.0.0")
    parser.add_argument("--adapter", choices=["json_file", "sqlite"], default="json_file")
    parser.add_argument("--home", type=Path, default=None)
    args = parser.parse_args()

    store = load_adapter(args.adapter)
    if args.home:
        store.home = args.home
        store.home.mkdir(parents=True, exist_ok=True)
        if hasattr(store, "db_path"):
            store.db_path = store.home / "storage.db"
    banner()

    current_session = None

    while True:
        try:
            raw = input("SP> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        if not raw:
            continue

        # Strip leading 'SP ' prefix if entered
        if raw.upper().startswith("SP "):
            raw = raw[3:].strip()
            if not raw:
                continue

        parts = raw.split(maxsplit=1)
        cmd = parts[0].upper()
        payload = parts[1] if len(parts) > 1 else ""

        if cmd in ("HELP", "?"):
            print("\nAvailable commands:")
            for c, doc in COMMANDS.items():
                print(f"  SP {c:<15} {doc}")
            print()
        elif cmd == "RECALL":
            current_session = cmd_recall(store, payload)
        elif cmd == "SAVE":
            if not current_session:
                print("[!] No active session. Run SP recall first.")
                continue
            cmd_save(store, current_session, payload)
        elif cmd in ("PONYTAIL", "LAZY"):
            cmd_ponytail(store, current_session, payload)
        elif cmd == "FACT":
            cmd_fact(store, payload)
        elif cmd in ("TIER-CHECK", "TIER", "ROUTE-MODEL"):
            cmd_tier_check(payload)
        elif cmd == "LOOP-GUARD":
            cmd_loop_guard(store, current_session, payload)
        elif cmd == "COMPACT":
            cmd_compact(store, current_session, payload)
        elif cmd == "MEMORY":
            cmd_memory(store, payload)
        elif cmd == "MARK-DONE":
            if not current_session:
                print("[!] No active session.")
                continue
            cmd_mark_done(store, current_session)
        elif cmd in ("LIST", "SESSIONS"):
            cmd_list(store, payload)
        elif cmd == "DELETE":
            if not payload:
                print("[!] Usage: SP delete SESSION_ID")
                continue
            cmd_delete(store, payload)
        elif cmd == "BUDGET":
            cmd_budget(store, payload)
        elif cmd == "FIND":
            if not payload:
                print("[!] Usage: SP find \"keywords\"")
                continue
            cmd_find(store, payload)
        elif cmd == "LIST-SKILLS":
            cmd_list_skills(store, payload)
        elif cmd == "PERSIST":
            cmd_persist(store, payload)
        elif cmd == "EXIT":
            print("Goodbye.")
            break
        else:
            print(f"[!] Unknown command: {cmd!r}  (type 'help' for options)")


if __name__ == "__main__":
    main()
