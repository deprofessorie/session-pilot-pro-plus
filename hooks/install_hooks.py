#!/usr/bin/env python3
"""
Session Pilot Pro Plus — Hook Installer
========================================
Registers lifecycle hooks for Claude Code and local harnesses.
Complies strictly with Claude Code hooks JSON schema:
  - Hooks dictionary containing event arrays
  - Matcher objects with nested hook command definitions
  - Events: SessionStart, Stop, and PostToolUse (matcher: Bash)
"""

import json
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
HOOKS_DIR = ROOT_DIR / "hooks"


def install_claude_code():
    claude_dir = Path.home() / ".claude"
    if not claude_dir.exists():
        claude_dir.mkdir(parents=True, exist_ok=True)

    settings_file = claude_dir / "settings.json"
    settings = {}
    if settings_file.exists():
        try:
            settings = json.loads(settings_file.read_text(encoding="utf-8"))
        except Exception:
            settings = {}

    hooks = settings.setdefault("hooks", {})
    python_exe = sys.executable

    # SessionStart event
    hooks["SessionStart"] = [
        {
            "hooks": [
                {
                    "type": "command",
                    "command": f'"{python_exe}" "{HOOKS_DIR / "session_start.py"}"'
                }
            ]
        }
    ]

    # Stop event (Claude Code session termination)
    hooks["Stop"] = [
        {
            "hooks": [
                {
                    "type": "command",
                    "command": f'"{python_exe}" "{HOOKS_DIR / "session_stop.py"}"'
                }
            ]
        }
    ]

    # PostToolUse event (harvests facts from Bash executions)
    hooks["PostToolUse"] = [
        {
            "matcher": "Bash",
            "hooks": [
                {
                    "type": "command",
                    "command": f'"{python_exe}" "{HOOKS_DIR / "post_tool_use.py"}"'
                }
            ]
        }
    ]

    settings_file.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    print(f"✓ Claude Code hooks configured in {settings_file}")
    print("  - SessionStart: auto-recalls prior state")
    print("  - Stop: safe, non-destructive flush")
    print("  - PostToolUse (Bash): auto-harvests test/build command facts")


def main():
    print("Installing Session Pilot Pro Plus lifecycle hooks...")
    try:
        install_claude_code()
    except Exception as e:
        print(f"✗ Claude Code setup: {e}")

    print("\nHooks installation complete.")


if __name__ == "__main__":
    main()
