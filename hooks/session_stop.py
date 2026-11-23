#!/usr/bin/env python3
"""
Session Pilot Pro Plus — Non-Destructive Session Stop Hook
===========================================================
Executes when an agent session ends (Stop event in Claude Code).
CRITICAL: Non-destructive design.
Does NOT overwrite existing checkpoints or done/next actions.
Safely flushes and preserves existing task state.
"""

import os
import sys
import time
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


def main():
    if not store:
        sys.exit(0)

    # Resolve session id safely
    sys.path.insert(0, str(ROOT_DIR / "scripts"))
    try:
        from sp import get_current_session_id
        session_id = get_current_session_id()
    except Exception:
        session_id = os.environ.get("SESSION_PILOT_ID")

    if not session_id:
        sys.exit(0)

    state = store.load(session_id)
    if not state:
        # No existing state: do not manufacture false checkpoints
        sys.exit(0)

    # Touch updated_at timestamp without modifying or appending to checkpoints
    checkpoints = state.get("checkpoints", [])
    store.save(session_id, checkpoints=checkpoints)
    sys.exit(0)


if __name__ == "__main__":
    main()
