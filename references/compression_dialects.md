# Context Compaction & Caveman Dialect

> Mechanism Classification:
> - **Store Compaction:** ● Enforced natively via storage adapters (`sp.py compact`).
> - **Harness Context Compaction:** ◐ Prompt / host command advisory (`/compact`).
> - **Caveman Dialect:** ◐ Prompt-advisory mode for extreme output token conservation.

---

## 1. Store Compaction (`SP compact`)

### Mechanism (● Native Store)
`sp.py compact --keep N` trims the session store's checkpoint array to the most recent $N$ entries (default: 5), purging stale history while keeping the session file compact and fast.

> **Note:** This compacts Session Pilot's stored checkpoints. Harness-level context window compaction depends on the host's slash command (e.g. `/compact` in Claude Code/Antigravity).

```bash
python scripts/sp.py compact [--session <id>] [--keep 5]
```

---

## 2. Caveman Dialect (`SP caveman`)

### Mechanism (◐ Prompt Advisory)
An ultra-dense dialect instruction inspired by the Caveman project (Terminal-Bench 4: 33.2% input token reduction, 21% cheaper per solved task).

- **Rule:** Strip conversational filler, greetings, and pleasantries.
- **Accuracy:** Maintain 100% precision on code, paths, errors, and commands.
- **Activation:** Set style in session via `sp.py save --style caveman` or include in turn instruction.
