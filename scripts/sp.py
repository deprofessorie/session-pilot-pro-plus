#!/usr/bin/env python3
"""
Session Pilot Pro Plus — Unified CLI (sp.py)
=============================================
Fast, zero-dependency CLI for agent bootstrap and turn execution:
  - sp.py recall [--session <id>]
  - sp.py find "<keywords>" [-k 5]
  - sp.py save --done "..." --next "..."
  - sp.py fact [set|get|list|delete]
  - sp.py ponytail [lite|full|ultra|off]
  - sp.py tier-check "<task>"
"""

import argparse
import hashlib
import json
import os
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
except Exception as e:
    store = None


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
    delta = int(time.time() - ts)
    if delta < 60:
        return f"{delta}s ago"
    if delta < 3600:
        return f"{delta // 60}m ago"
    if delta < 86400:
        return f"{delta // 3600}h ago"
    return f"{delta // 86400}d ago"


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
        print(f"- [{ago}] done: {cp.get('done')} | next: {cp.get('next')}")
    if state.get("ponytail_mode"):
        print(f"ponytail_mode: {state['ponytail_mode']}")
    if state.get("style"):
        print(f"style: {state['style']}")


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
                # read first 15 lines of frontmatter
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
    if args.action == "set":
        store.fact_set(proj, args.key, args.value)
        print(f"[fact set] {args.key} = {args.value!r}")
    elif args.action == "get":
        val = store.fact_get(proj, args.key)
        print(f"[fact get] {args.key} = {val!r}")
    elif args.action == "list":
        facts = store.fact_list(proj)
        print(f"[Verified Repo Facts ({len(facts)})]:")
        for k, v in facts.items():
            print(f"  • {k}: {v}")
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
    if any(w in task for w in ["hi", "hello", "what is", "look up", "typo"]):
        print("[Tier] T0 (Trivial) -> Direct answer, cheap model (flash_lite / flash), 0 tools")
    elif any(w in task for w in ["read", "find", "grep", "search", "list", "convert"]):
        print("[Tier] T1 (Mechanical) -> Cheap model (flash)")
    elif any(w in task for w in ["feature", "implement", "fix", "test", "refactor"]):
        print("[Tier] T2 (Standard) -> Standard model (pro / self)")
    else:
        print("[Tier] T3 (Hard) -> Flagship reasoning model (complex architecture / security)")


def main():
    parser = argparse.ArgumentParser(description="Session Pilot Pro Plus CLI")
    subparsers = parser.add_subparsers(dest="command")

    # recall
    p_recall = subparsers.add_parser("recall")
    p_recall.add_argument("--session", default=None)

    # save
    p_save = subparsers.add_parser("save")
    p_save.add_argument("--session", default=None)
    p_save.add_argument("--done", default="")
    p_save.add_argument("--next", default="")
    p_save.add_argument("--style", default=None)
    p_save.add_argument("--global-style", default=None)
    p_save.add_argument("--ponytail", default=None)

    # find
    p_find = subparsers.add_parser("find")
    p_find.add_argument("keywords")
    p_find.add_argument("-k", type=int, default=5)

    # fact
    p_fact = subparsers.add_parser("fact")
    p_fact.add_argument("action", choices=["set", "get", "list", "delete"])
    p_fact.add_argument("key", nargs="?", default=None)
    p_fact.add_argument("value", nargs="?", default=None)
    p_fact.add_argument("--project", default="default")

    # ponytail
    p_pony = subparsers.add_parser("ponytail")
    p_pony.add_argument("mode", choices=["lite", "full", "ultra", "off"], default="full", nargs="?")
    p_pony.add_argument("--session", default=None)

    # tier-check
    p_tier = subparsers.add_parser("tier-check")
    p_tier.add_argument("task")

    args = parser.parse_args()
    if args.command == "recall":
        cmd_recall(args)
    elif args.command == "save":
        cmd_save(args)
    elif args.command == "find":
        cmd_find(args)
    elif args.command == "fact":
        cmd_fact(args)
    elif args.command == "ponytail":
        cmd_ponytail(args)
    elif args.command == "tier-check":
        cmd_tier_check(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
