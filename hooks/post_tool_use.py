#!/usr/bin/env python3
"""
Session Pilot Pro Plus — PostToolUse Fact Harvesting Hook
==========================================================
Executes after tool calls (specifically Bash command executions).
Complies with Claude Code PostToolUse hook specification:
  - Reads hook JSON payload from stdin
  - Fallback: parses command string passed via CLI arguments
  - Automatically harvests build, test, and package manager facts into store
"""

import json
import os
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
ADAPTERS_DIR = ROOT_DIR / "adapters"
sys.path.insert(0, str(ADAPTERS_DIR))

try:
    import json_file
    store = json_file.get_store()
except Exception:
    store = None


def get_project_name() -> str:
    # Use git root directory name or current working directory name
    cwd = Path.cwd()
    cur = cwd
    while cur != cur.parent:
        if (cur / ".git").exists():
            return cur.name
        cur = cur.parent
    return cwd.name or "default"


HARVEST_RULES = [
    # (Category, regex_pattern, key_name)
    ("test", re.compile(r'\b(pytest(\s+[\w\-\/\.]+)*)\b', re.IGNORECASE), "test_cmd"),
    ("test", re.compile(r'\b(vitest(\s+run)?)\b', re.IGNORECASE), "test_cmd"),
    ("test", re.compile(r'\b((?:pnpm|npm|yarn|bun)\s+(?:run\s+)?test(?::\w+)?)\b', re.IGNORECASE), "test_cmd"),
    ("test", re.compile(r'\b(cargo\s+test(\s+[\w\-\:]+)*)\b', re.IGNORECASE), "test_cmd"),
    ("test", re.compile(r'\b(go\s+test(\s+[\w\-\.\/]+)*)\b', re.IGNORECASE), "test_cmd"),
    ("build", re.compile(r'\b((?:pnpm|npm|yarn|bun)\s+(?:run\s+)?build(?::\w+)?)\b', re.IGNORECASE), "build_cmd"),
    ("build", re.compile(r'\b(cargo\s+build(\s+--release)?)\b', re.IGNORECASE), "build_cmd"),
    ("build", re.compile(r'\b(go\s+build(\s+[\w\-\.\/]+)*)\b', re.IGNORECASE), "build_cmd"),
    ("build", re.compile(r'\b(mvn\s+(?:clean\s+)?compile|gradle\s+build)\b', re.IGNORECASE), "build_cmd"),
    ("linter", re.compile(r'\b(ruff\s+(?:check|format)|eslint|clippy|black|mypy)\b', re.IGNORECASE), "linter_cmd"),
]


def harvest_command(cmd_str: str, project: str = None, store_override=None):
    active_store = store_override or store
    if not active_store or not cmd_str or not isinstance(cmd_str, str):
        return {}

    proj = project or get_project_name()
    harvested = {}

    # Check package manager presence
    if re.search(r'\bpnpm\b', cmd_str):
        active_store.fact_set(proj, "pkg_manager", "pnpm")
        harvested["pkg_manager"] = "pnpm"
    elif re.search(r'\byarn\b', cmd_str):
        active_store.fact_set(proj, "pkg_manager", "yarn")
        harvested["pkg_manager"] = "yarn"
    elif re.search(r'\bbun\b', cmd_str):
        active_store.fact_set(proj, "pkg_manager", "bun")
        harvested["pkg_manager"] = "bun"
    elif re.search(r'\bcargo\b', cmd_str):
        active_store.fact_set(proj, "pkg_manager", "cargo")
        harvested["pkg_manager"] = "cargo"

    # Match command patterns
    for category, pattern, key in HARVEST_RULES:
        m = pattern.search(cmd_str)
        if m:
            matched_val = m.group(1).strip()
            active_store.fact_set(proj, key, matched_val)
            harvested[key] = matched_val

    return harvested


def main():
    cmd_to_parse = ""

    # 1. Try reading Claude Code JSON payload from stdin
    if not sys.stdin.isatty():
        try:
            stdin_data = sys.stdin.read().strip()
            if stdin_data:
                payload = json.loads(stdin_data)
                # Claude Code PostToolUse format: tool_input dict containing 'command'
                tool_input = payload.get("tool_input", {})
                if isinstance(tool_input, dict):
                    cmd_to_parse = tool_input.get("command", "")
                elif isinstance(tool_input, str):
                    cmd_to_parse = tool_input
        except Exception:
            pass

    # 2. Fallback to CLI argument if stdin was empty
    if not cmd_to_parse and len(sys.argv) > 1:
        cmd_to_parse = " ".join(sys.argv[1:])

    if cmd_to_parse:
        results = harvest_command(cmd_to_parse)
        if results:
            print(f"[SP PostToolUse] Harvested repo facts: {results}")

    sys.exit(0)


if __name__ == "__main__":
    main()
