# Tool Pruning & Loop Guard

> Inspired by TokenEconomizer cost-control mechanisms. Operates inline without auxiliary LLM judge calls.

## 1. Tool Schema Pruning (`SP prune-tools`)

### Problem
Large MCP setups inject dozens of tool definitions (often 100–300 tokens per tool schema) into every turn's system payload, wasting 2,000–5,000 tokens on tools irrelevant to the active task.

### Commands
- `SP prune-tools show` — List available tools and mark active vs inactive candidates.
- `SP prune-tools apply` — Suppress schemas of unused tools for the current session phase.
- `SP prune-tools auto` — Dynamically drop tool definitions not called in the last 3 turns.
- `SP prune-tools restore` — Restore visibility of all available tools.

---

## 2. Loop Guard & Circuit Breaker (`SP loop-guard`)

### Problem
Agents frequently get trapped in retry cycles (e.g. running the same failing test 4 times with slight syntactic variations). TokenEconomizer uses an auxiliary LLM judge call; Session Pilot detects cycles **inline**.

### Commands & Signals
- `SP loop-guard status` — Check current repetition counters and pattern hashes.
- `SP loop-guard nudge` — Propose an alternate hypothesis when 2 identical failures occur.
- `SP loop-guard break` — Circuit-breaker: immediately halt execution when a failure repeats 3+ times.
- `SP loop-guard auto` — Activate inline pattern inspection across command outputs.
