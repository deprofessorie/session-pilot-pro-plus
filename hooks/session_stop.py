#!/usr/bin/env python3
"""
Session Pilot Pro Plus — Session Stop Lifecycle Hook
=====================================================
Executes automatically when an agent session terminates.
Ensures the final state is checkpointed to disk.
"""

import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
SP_PY = ROOT_DIR / "scripts" / "sp.py"


def main():
    session_id = os.environ.get("SESSION_PILOT_ID")
    cmd = [
        sys.executable, str(SP_PY), "save",
        "--done", "Session concluded cleanly via lifecycle hook",
        "--next", "Resume on next session start"
    ]
    if session_id:
        cmd.extend(["--session", session_id])

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if proc.stdout:
            sys.stdout.write(proc.stdout)
        sys.exit(proc.returncode)
    except Exception as e:
        sys.stderr.write(f"[SP Hook Error] Failed to run session_stop: {e}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
