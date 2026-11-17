---
name: session-pilot-pro-plus
description: Professional, token-aware session memory & skill router. Adds agent-side token budgeting, optional micro-skills, tool-prune, loop-guard, and lightweight search/persistence helpers. Prompt-only; no external dependencies.
license: MIT
metadata:
  version: "1.0.0"
---

# Session Pilot Pro Plus

A lightweight core (< 200 tokens) that **recalls**, **routes**, **checkpoints**, and **budget-checks** every turn. Optional sub-skills are loaded on demand, keeping the base prompt tiny.

All `SP` commands are **chat conventions**: the user types them in conversation and the agent performs the described behavior. They are not shell commands, and this skill ships no executable code.

## Core Commands (always loaded)
1. **Recall** – `SP recall [--session ID]` – restores prior chat state or starts a fresh session.
2. **Route** – `SP find "<keywords>"` – selects the best installed skill. Returns `match: strong|weak|none`.
3. **Checkpoint** – `SP save --done "<action>" --next "<step>"` – stores progress for later resumption.
4. **Import** – `SP import <PATH>` – wires project-level rules into the session.
5. **Token-Budget** – `SP budget --limit <max-tokens>` – the agent estimates token usage for the upcoming turn itself (word count × ~1.33; no external library or tooling). If the projected total exceeds the limit, the skill responds with a concise suggestion to prune context.

## Optional Sub-Skills (on-demand, **not** part of the core prompt)

These helpers are self-contained instructions. The project names below are inspiration, not dependencies — nothing extra needs to be installed.

### Micro-Skills (inspired by TokenEconomizer)
- `SP micro-skill <name>` – runs a tiny helper that performs a single focused action (e.g., quick code lint, dependency check). Each call adds **~30 tokens** (estimate).

### Tool-Prune
- `SP prune-tools` – reviews the current turn's tool usage and drops unused tool calls from the context, saving an estimated **~20-40 tokens** per turn.

### Loop-Guard
- `SP loop-guard` – detects repetitive patterns (e.g., endless retry loops) and suggests breaking the cycle, avoiding an estimated **~50-80 extra tokens** from duplicated model calls.

### Optional Model Calls
- `SP call-model <model>` – on-demand invocation of a secondary LLM for specialized tasks, if the host agent supports it. **Disabled by default**; only incurs tokens when explicitly requested.

These additions are **opt-in**: they are only loaded when you invoke the corresponding command, keeping the core prompt at ~180 tokens (estimate).

### Semantic Search (inspired by code-session-memory)
- `SP index <PATH>` – builds a lightweight searchable summary of file contents using the host agent's available storage.
- `SP query "<natural-language>"` – returns top-3 relevant snippets.
- **Cost:** ~140 tokens when indexing; ~20 tokens per query (estimates).

### Tiny Persistent Store (inspired by ck)
- `SP persist set <key> <value>` – write a small JSON value per project.
- `SP persist get <key>` – retrieve it.
- **Cost:** +50 tokens just to describe the command (estimate).

### Unified Memory (inspired by unified-memory)
- `SP memory sync` – syncs durable cross-agent context.
- **Cost:** ~30 tokens (estimate); useful for long-running multi-agent workflows.

### Micro-Skill Router (inspired by session-pilot-lite)
- Simple keyword-based routing rules. No extra tokens when not used.

## Token-Budget Mechanics
- The **budget** command is an **agent-side estimate** — no external tokenizer, library, or model call is involved. The agent counts words in the upcoming user prompt, the accumulated context, and any loaded sub-skill descriptors, and multiplies by ~1.33.
- If `estimated_total > limit`, the skill returns:
  ```
  [!] Token budget exceeded (estimated X > limit Y). Suggested actions:
   - Trim recall history (`SP save --prune`)
   - Disable optional sub-skill(s) (`SP disable <name>`)
   - Summarize large chunks (`SP summarize <path>`)
  ```
- Users can raise the limit with `SP budget --limit <new>` or accept the suggestion.
- Estimates are approximate and vary by model and tokenizer.

## Token Cost Summary (design estimates, not measured benchmarks)
| Component | Approx. Tokens |
|---|---|
| Core prompt | ~180 |
| Token-budget check | +30 |
| Semantic index (once) | +140 |
| Persistent store init | +50 |
| **Maximum** (all extras) | **~410** |

## Usage Example
```text
User: "Add a new API endpoint to fetch user stats."
SP budget --limit 300           # checks budget
SP recall --session 2023-projA  # restores state
SP find "api backend python"    # routes to your custom backend skill
SP index src/                   # optional: index source files for later queries
SP save --done "generated endpoint" --next "write tests"
```

## When to Enable Optional Features
- **Semantic search** – large codebases where keyword routing misses relevant files.
- **Persistent store** – need to remember a flag (e.g., chosen framework) across sessions.
- **Unified memory** – multi-agent pipelines that share context.
- All are **opt-in**: if you never call them, they never add tokens.

---
