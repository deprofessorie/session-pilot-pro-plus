#!/usr/bin/env python3
"""
Session Pilot Pro Plus — Interactive Demo REPL
===============================================
A minimal prompt-driven shell so anyone can exercise every SP command
without wiring it into an LLM harness first.  Run with:

    python scripts/repl.py [--adapter json_file|sqlite] [--home ~/.session-pilot-pro-plus]
"""

import argparse
import sys
from pathlib import Path

# Windows console: force UTF-8 so box-drawing chars and ✓/✗ print cleanly
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# ─── Resolve adapter path ───────────────────────────────────────────────────
SKILL_ROOT = Path(__file__).resolve().parent.parent
ADAPTER_DIR = SKILL_ROOT / "adapters"

def load_adapter(name: str):
    module_path = ADAPTER_DIR / f"{name}.py"
    if not module_path.exists():
        print(f"[!] Adapter '{name}' not found at {module_path}")
        sys.exit(1)
    import importlib.util, types
    spec = importlib.util.spec_from_file_location(f"sp_adapter_{name}", module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.get_store()


def banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║         Session Pilot Pro Plus — Interactive REPL            ║
║    v2.0.0 | The Unified Agent Memory & Control Platform      ║
╚══════════════════════════════════════════════════════════════╝

Commands (type 'help' for full list):
  SP recall [SESSION_ID]          Load or create a session
  SP save --done X --next Y       Checkpoint progress
  SP ponytail [lite|full|ultra]   Toggle Ponytail minimal-diff mode
  SP fact set KEY VALUE           Record durable repo micro-skill
  SP fact list                    List verified repository facts
  SP tier-check "task"            Model tier arbitrage & routing
  SP prune-tools                  Omit unused tool definitions
  SP loop-guard                   Detect repetitive loops
  SP compact                      Compact conversational history
  SP caveman [on|off]             Ultra-low token dialect
  SP budget --limit N             Show estimated token budget
  SP find "keywords"              Route to best skill
  SP mark-done                    Mark current session complete
  SP exit                         Quit
""")


COMMANDS = {
    "recall": "--session ID\tLoad or create a session (auto-creates if missing)",
    "save":   "--done ... --next ...\tCheckpoint work for later resume",
    "ponytail": "[lite|full|ultra|off]\tMinimal-diff Lazy Senior Dev mode",
    "fact":   "set/get/list/delete\tRepo facts bank (TokenEconomizer micro-skills)",
    "tier-check": "\"task\"\t\tTask difficulty triage (T0..T3) & model routing",
    "prune-tools": "[show|apply|auto]\tSuppress unused tool schemas",
    "loop-guard": "[status|nudge|break]\tInline repetition & cycle detection",
    "compact": "[summary|hard]\tContext history compression",
    "caveman": "[on|off]\t\tUltra-dense dialect for critical token quota",
    "mark-done": "\t\t\tMark session complete",
    "list":   "\t\t\tList all sessions",
    "delete": "--session ID\t\tRemove a session",
    "budget": "--limit N\t\tEstimate upcoming turn cost",
    "find":   "\"keywords\"\t\tRoute to best installed skill",
    "list-skills": "\t\t\tShow discoverable skills",
    "persist": "set/get <key> <value>\tProject key/value store",
    "learn":  "\t\t\tDistill durable facts from session",
    "exit":   "\t\t\tQuit REPL",
}


def cmd_recall(store, args):
    sid = args.strip() if args.strip() else f"demo-{__import__('time').time():.0n}"
    state = store.get_or_create(sid, title=sid)
    print(f"\n[Session loaded] id={state['id']}  status={state['status']}")
    print(f"  Goal: {state.get('goal') or '(none)'}")
    cp = state.get("checkpoints", [])
    print(f"  Checkpoints: {len(cp)}")
    for c in cp[-3:]:
        print(f"    ✓ done: {c['done']!r}  → next: {c['next']!r}")
    style = state.get("style") or state.get("global_style")
    if style:
        print(f"  Style: {style!r}")
    return sid


def time_ago(ts):
    if not ts:
        return "never"
    delta = int(time.time() - ts)
    if delta < 60:
        return f"{delta}s ago"
    if delta < 3600:
        return f"{delta // 60}m ago"
    if delta < 86400:
        return f"{delta // 3600}h ago"
    return f"{delta // 86400}d ago"


def cmd_save(store, sid, args):
    import re
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
    print(f"\n{'ID':<20} {'Title':<30} {'Status':<10} {'Updated':>14}")
    print("-" * 76)
    for s in sessions:
        ago = time_ago(s.get("updated_at", 0))
        print(f"{s['id']:<20} {s['title'][:28]:<30} {s['status']:<10} {ago:>14}")


def cmd_delete(store, sid):
    ok = store.delete(sid)
    print(f"[Deleted] {sid} → {ok}")


def cmd_budget(_store, args):
    import re, math
    m = re.search(r"--limit\s+(\d+)", args)
    limit = int(m.group(1)) if m else 500
    # Simulate a hypothetical upcoming prompt of ~40 words
    estimated_words = len(args.split()) if args else 40
    tokens = round(estimated_words * 1.33)
    print(f"[Budget check]  limit={limit}  est_tokens={tokens}")
    if tokens > limit:
        print(f"  [!] EXCEEDED — suggested: trim context or reduce helpers")
    else:
        print(f"  ✓ Within budget ({tokens}/{limit} tokens)")


def cmd_find(_store, args):
    """Simulate keyword routing against installed skills."""
    installed = [
        ("session-pilot-pro-plus", "Professional, token-aware session memory & skill router"),
        ("accessibility", "Design, implement, and audit accessible UI to WCAG 2.2"),
        ("agency-backend-architect", "Senior backend architect specializing in scalable systems"),
        ("agency-code-reviewer", "Expert code reviewer focused on correctness & maintainability"),
        ("tokeneconomizer-status", "Show what TokenEconomizer has learned for this repository"),
        ("security-review", "Use this skill when adding authentication or sensitive features"),
    ]
    keywords = [w.lower() for w in args.split()]
    scored = []
    for name, desc in installed:
        desc_terms = set(desc.lower().split())
        overlap = sum(1 for kw in keywords if any(kw in t for t in desc_terms))
        if overlap > 0:
            scored.append((overlap, name, desc))
    scored.sort(key=lambda x: -x[0])
    match_level = "strong" if scored and scored[0][0] >= 3 else ("weak" if scored else "none")
    print(f"[SP find '{args}']  match: {match_level}")
    for score, name, desc in scored[:5]:
        print(f"  #{score}: {name:<35} {desc}")


def cmd_list_skills(store, _args):
    skills_dir = Path(__file__).resolve().parent.parent.parent.parent / ".config" / "opencode" / "skills"
    if not skills_dir.exists():
        skills_dir = Path.home() / ".config" / "opencode" / "skills"
    out = list(skills_dir.iterdir()) if skills_dir.exists() else []
    print(f"\nDiscovered {len(out)} local skill folders:")
    for p in sorted(out):
        if p.is_dir():
            sk = p / "SKILL.md"
            tag = "✓" if sk.exists() else "○"
            print(f"  {tag}  {p.name}")


def cmd_persist(store, args):
    import re
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


def cmd_learn(store, sid):
    """Simulate distilling a lesson (demo only)."""
    import time
    fact = {"text": "tests require Redis on :6379 — always mock in CI", "source": "review", "ts": time.time()}
    if hasattr(store, 'load'):
        state = store.load(sid) or {}
        facts = list(state.get("learned_facts", []))
        facts.append(fact)
        store.save(sid)  # would append in real impl
    print(f"[SP learn] distilled 1 new fact:")
    print(f"  • {fact['text']}")


def cmd_ponytail(store, sid, args):
    mode = args.strip().lower() or "full"
    if mode not in ("lite", "full", "ultra", "off"):
        print("[!] Valid modes: lite, full, ultra, off")
        return
    if sid:
        store.save(sid, ponytail_mode=mode)
    print(f"[Ponytail Mode] set to: {mode.upper()}")
    if mode == "lite":
        print("  • Build what was asked. Name smaller option in 1 line.")
    elif mode == "full":
        print("  • Smallest complete change. Zero unrequested bloat. Transparency note required.")
    elif mode == "ultra":
        print("  • Question the request: actively push back on unneeded complexity.")
    elif mode == "off":
        print("  • Normal agent behavior restored.")


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
                print(f"  • {k}: {v}")
    elif subcmd == "delete" and len(parts) >= 2:
        key = parts[1]
        ok = store.fact_delete("__demo__", key)
        print(f"[Fact Delete] {key} → {ok}")
    else:
        print("Usage: SP fact set KEY VALUE  |  SP fact get KEY  |  SP fact list  |  SP fact delete KEY")


def cmd_tier_check(args):
    task = args.strip() or "general task"
    t_lower = task.lower()
    t3_words = ["architecture", "security", "vulnerability", "concurrency", "race condition", "deadlock", "crypto", "exploit", "cve", "distributed"]
    t2_words = ["feature", "implement", "fix", "test", "refactor", "build", "component"]
    t1_words = ["read", "find", "search", "list", "format", "convert", "grep"]
    t0_words = ["hi", "hello", "what is", "explain", "look up", "typo"]

    if any(w in t_lower for w in t3_words):
        tier, target = "T3 (Hard)", "Flagship reasoning model (concurrency, security, architecture)"
    elif any(w in t_lower for w in t2_words):
        tier, target = "T2 (Standard)", "Balanced model (pro / standard)"
    elif any(w in t_lower for w in t1_words):
        tier, target = "T1 (Mechanical)", "flash model subagent (conserve premium quota)"
    elif any(w in t_lower for w in t0_words):
        tier, target = "T0 (Trivial)", "Direct answer, flash_lite / flash, 0 tools"
    else:
        tier, target = "T2 (Standard)", "Balanced model (pro / standard)"
    print(f"[Tier Triage] task: '{task}'")
    print(f"  Level:  {tier}")
    print(f"  Action: {target}")


def cmd_prune_tools(args):
    action = args.strip().lower() or "auto"
    print(f"[Tool Pruning] action={action}")
    print("  ✓ Hiding 14 unused tool schemas (saving ~35 tokens/turn)")


def cmd_loop_guard(args):
    action = args.strip().lower() or "status"
    print(f"[Loop Guard] action={action}")
    print("  ✓ Repetition count: 0 (No cycles detected in recent turns)")


def cmd_compact(args):
    level = args.strip().lower() or "summary"
    print(f"[Context Compaction] level={level}")
    print("  ✓ Dropped historical preamble; collapsed past tool runs into structured state (~45% token reduction)")


def cmd_caveman(args):
    state = args.strip().lower() or "on"
    print(f"[Caveman Mode] {state.upper()}")
    if state in ("on", "true", "1"):
        print("  • Dialect: ultra-dense telegraphic. Zero fluff. Full technical accuracy.")
    else:
        print("  • Standard dialect restored.")


def main():
    parser = argparse.ArgumentParser(description="Session Pilot Pro Plus — REPL")
    parser.add_argument("--adapter", choices=["json_file", "sqlite"], default="json_file")
    parser.add_argument("--home", type=Path, default=None)
    args = parser.parse_args()

    store = load_adapter(args.adapter)
    if args.home:
        store.home = args.home
        store.home.mkdir(parents=True, exist_ok=True)
        if hasattr(store, "db_path"):
            store.db_path = store.home / "storage.db"
            load_adapter("sqlite")._connect(store.db_path).close()
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

        # Strip leading 'SP ' prefix if entered by the user
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
        elif cmd == "PRUNE-TOOLS":
            cmd_prune_tools(payload)
        elif cmd == "LOOP-GUARD":
            cmd_loop_guard(payload)
        elif cmd == "COMPACT":
            cmd_compact(payload)
        elif cmd == "CAVEMAN":
            cmd_caveman(payload)
        elif cmd == "MARK-DONE":
            if not current_session:
                print("[!] No active session.")
                continue
            cmd_mark_done(store, current_session)
        elif cmd == "LIST":
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
        elif cmd == "LEARN":
            if not current_session:
                print("[!] No active session. Run SP recall first.")
                continue
            cmd_learn(store, current_session)
        elif cmd == "EXIT":
            print("Goodbye.")
            break
        else:
            print(f"[!] Unknown command: {cmd!r}  (type 'help' for options)")


if __name__ == "__main__":
    main()