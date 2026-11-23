#!/usr/bin/env python3
"""
Session Pilot Pro Plus — Hook Installer
========================================
Registers lifecycle hooks for Claude Code, OpenCode, and shell integrations.
Generates harness configuration files so session persistence is natively enforced (●).
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

    hooks["SessionStart"] = f'"{python_exe}" "{HOOKS_DIR / "session_start.py"}"'
    hooks["SessionStop"] = f'"{python_exe}" "{HOOKS_DIR / "session_stop.py"}"'

    settings_file.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    print(f"✓ Claude Code hooks configured in {settings_file}")


def install_opencode():
    opencode_dir = Path.home() / ".config" / "opencode"
    if not opencode_dir.exists():
        opencode_dir.mkdir(parents=True, exist_ok=True)

    hooks_file = opencode_dir / "hooks.json"
    python_exe = sys.executable
    config = {
        "on_session_start": f'"{python_exe}" "{HOOKS_DIR / "session_start.py"}"',
        "on_session_stop": f'"{python_exe}" "{HOOKS_DIR / "session_stop.py"}"',
    }
    hooks_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"✓ OpenCode hooks configured in {hooks_file}")


def main():
    print("Installing Session Pilot Pro Plus lifecycle hooks...")
    try:
        install_claude_code()
    except Exception as e:
        print(f" Claude Code setup: {e}")

    try:
        install_opencode()
    except Exception as e:
        print(f" OpenCode setup: {e}")

    print("\nHooks installation complete.")


if __name__ == "__main__":
    main()
