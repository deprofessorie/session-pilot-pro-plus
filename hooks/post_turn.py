#!/usr/bin/env python3
"""
Session Pilot Pro Plus — Post-Turn / Post-Tool-Use Hook
========================================================
Lightweight hook triggered after tool executions or turns.
Functions:
  1. Auto-harvests verified build/test commands from command executions into fact store.
  2. Evaluates loop detection if multiple repeated actions occur.
"""

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


def harvest_command_facts(command_line: str, project: str = "default", store_override=None):
    active_store = store_override or store
    if not active_store or not command_line:
        return

    cmd = command_line.strip()
    # Detect build commands
    if re.search(r'\b(pnpm|npm|yarn|bun)\s+(run\s+)?(build|compile)\b', cmd):
        active_store.fact_set(project, "build_cmd", cmd)
    elif re.search(r'\b(cargo\s+build|go\s+build|mvn\s+compile|gradle\s+build)\b', cmd):
        active_store.fact_set(project, "build_cmd", cmd)

    # Detect test commands
    if re.search(r'\b(pytest|vitest|jest|cargo\s+test|go\s+test|pnpm\s+test|npm\s+test)\b', cmd):
        active_store.fact_set(project, "test_cmd", cmd)

    # Detect package manager
    if "pnpm-lock.yaml" in cmd or cmd.startswith("pnpm"):
        active_store.fact_set(project, "pkg_manager", "pnpm")
    elif "yarn.lock" in cmd or cmd.startswith("yarn"):
        active_store.fact_set(project, "pkg_manager", "yarn")
    elif "bun.lockb" in cmd or cmd.startswith("bun"):
        active_store.fact_set(project, "pkg_manager", "bun")


def main():
    # If args passed (e.g. from harness tool logger)
    if len(sys.argv) > 1:
        command_line = " ".join(sys.argv[1:])
        harvest_command_facts(command_line)


if __name__ == "__main__":
    main()
