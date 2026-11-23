# Context Compaction & Caveman Dialect

> Inspired by Strategic-Compact and Caveman. High-density communication for quota constraints.

## 1. Context Compaction (`SP compact`)
- `SP compact summary` — Truncates conversational history down to active checkpoints, decisions, and uncommitted diffs.
- `SP compact hard` — Strips all preambles and collapses previous tool executions into one-line status indicators (~45% token reduction).

## 2. Caveman Dialect (`SP caveman`)
- `SP caveman on` — Activates ultra-dense telegraphic mode:
  - Eliminates pleasantries, filler phrases, and grammatical padding.
  - Maintains 100% technical, code, and architectural accuracy.
  - Generates 50–70% fewer output tokens.
- `SP caveman off` — Restores standard conversational mode.
