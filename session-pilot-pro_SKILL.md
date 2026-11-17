---
name: session-pilot-pro
description: Professional, token‑aware session memory & skill router. Adds automatic token budgeting via the `tokenizers` library, optional micro‑skill vector search, and tight integration of your custom skills (session‑pilot‑lite, code‑session‑memory, unified‑memory, ck).
license: MIT
metadata:
  version: "1.0.0"
---

# Session Pilot Pro

A lightweight core (< 200 tokens) that **recalls**, **routes**, **checkpoints**, and now **budget‑checks** every turn. Optional sub‑skills are loaded on demand, keeping the base prompt tiny.

## Core Commands (always loaded)
1. **Recall** – `SP recall [--session ID]` – restores prior chat state or starts a fresh session.
2. **Route** – `SP find "<keywords>"` – selects the best skill (≤ 5 ms). Returns `match: strong|weak|none`.
3. **Checkpoint** – `SP save --done "<action>" --next "<step>"` – stores progress for later resumption.
4. **Import** – `SP import <PATH>` – wires project‑level rules into the session.
5. **Token‑Budget** – `SP budget --limit <max‑tokens>` – computes estimated token usage for the upcoming turn using the **`tokenizers`** Python library (BPE compatible with the active model). If the projected total exceeds the limit, the skill aborts with a concise suggestion to prune context.

## Optional Sub‑Skills (on‑demand, **not** part of the core prompt)

### 🛠️ Micro‑Skills (from TokenEconomizer)
- `SP micro‑skill <name>` – runs a tiny helper that performs a single focused action (e.g., quick code lint, dependency check). Each call adds **~30 tokens**.

### 🧹 Tool‑Prune
- `SP prune-tools` – analyses the current turn’s tool usage and removes any unused tool calls from the context, saving **~20‑40 tokens** per turn.

### 🔁 Loop‑Guard
- `SP loop‑guard` – detects repetitive patterns (e.g., endless retry loops) and suggests breaking the cycle, avoiding **~50‑80 extra tokens** from duplicated model calls.

### 📡 Optional Model Calls
- `SP call‑model <model>` – on‑demand invocation of a secondary LLM for specialized tasks (e.g., code synthesis, reasoning). The call is **disabled by default** and only incurs tokens when explicitly requested.

These additions are **opt‑in**; they are only loaded when you invoke the corresponding command, keeping the core prompt at ~180 tokens.
### 🔍 Vector Semantic Search (from `code‑session‑memory`)
- `SP index <PATH>` – builds a tiny SQLite vector DB of file contents.
- `SP query "<natural‑language>"` – returns top‑3 relevant snippets.
- **Cost:** +140 tokens only when indexing; query adds ~20 tokens.

### 📦 Tiny Persistent Store (from `ck`)
- `SP persist set <key> <value>` – write a small JSON value per project.
- `SP persist get <key>` – retrieve it.
- **Cost:** +50 tokens just to describe the command.

### 🧠 Unified Memory (from `unified‑memory`)
- `SP memory sync` – syncs durable cross‑agent context.
- **Cost:** ~30 tokens; useful for long‑running multi‑agent workflows.

### ⚡ Micro‑Skill Router (your own `session‑pilot‑lite`)
- Leverages the ultra‑fast routing rules you already have. No extra tokens when not used.

## Token‑Budget Mechanics
- The **`budget`** command runs **client‑side** token estimation (no model call). It parses the upcoming user prompt, the accumulated system context, and any loaded sub‑skill descriptors.
- If `estimated_total > limit`, the skill returns:
  ```
  [!] Token budget exceeded (estimated  X  >  limit Y). Suggested actions:
   • Trim recall history (`SP save --prune`)
   • Disable optional sub‑skill(s) (`SP disable <name>`)
   • Summarize large chunks (`SP summarize <path>`)
  ```
- Users can raise the limit with `SP budget --limit <new>` or accept the suggestion.

## Performance Summary
| Component | Approx. Tokens | Latency |
|---|---|---|
| Core prompt | ~180 | < 5 ms |
| Token‑budget (client side) | +30 | < 1 ms |
| Vector index (once) | +140 | ~20 ms |
| Persistent store init | +50 | < 5 ms |
| **Maximum** (all extras) | **~410** | **< 30 ms** |

## Usage Example
```text
User: "Add a new API endpoint to fetch user stats."
SP budget --limit 300           # checks budget
SP recall --session 2023‑projA  # restores state
SP find "api backend python"   # routes to your custom backend skill
SP index src/                  # optional: index source files for later queries
SP save --done "generated endpoint" --next "write tests"
```

## When to Enable Optional Features
- **Vector search** – large codebases where keyword routing misses relevant files.
- **Persistent store** – need to remember a flag (e.g., chosen framework) across sessions.
- **Unified memory** – multi‑agent pipelines that share context.
- All are **opt‑in**: if you never call them, they never add tokens.

---
