---
name: session-pilot-pro-plus
description: Professional, token-aware session memory & skill router. Adds agent-side token budgeting, experience learning, rate-limit model fallback, optional micro-skills, tool-prune, loop-guard, and lightweight search/persistence helpers. Prompt-only; no external dependencies.
license: MIT
metadata:
  version: "1.3.0"
---

# Session Pilot Pro Plus

A lightweight core (< 200 tokens) that **recalls**, **routes**, **checkpoints**, and **budget-checks** every turn. Optional sub-skills are loaded on demand, keeping the base prompt tiny.

All `SP` commands are **chat conventions**: the user types them in conversation and the agent performs the described behavior. They are not shell commands, and this skill ships no executable code.

## Core Commands (always loaded)
1. **Recall** – `SP recall [--session ID]` – restores prior chat state (including learned facts, style, and checkpoints) or starts a fresh session.
   - `SP recall --list` – show available sessions (most recent first).
   - `SP recall --create "<id>"` – explicitly create a new session.
   - `SP recall --delete "<id>"` – remove an old session.
2. **Route** – `SP find "<keywords>"` – selects the best installed skill. Returns `match: strong|weak|none`.
   - `SP list` – show all discoverable skills/agents/plugins with one-line descriptions.
3. **Checkpoint** – `SP save --done "<action>" --next "<step>" [--style "..." [--global-style]] [--skill <name>]` – stores progress for later resumption; persists style preferences when provided.
4. **Import** – `SP import <PATH>` – wires project-level rules into the session.
5. **Token-Budget** – `SP budget --limit <max-tokens>` – the agent estimates token usage for the upcoming turn itself (word count × ~1.33; no external library or tooling). If the projected total exceeds the limit, the skill responds with a concise suggestion to prune context.
6. **Clean** – `SP clean` – drops low-value context (repeated self-replies, tool call echoes, old preamble) from the current turn's history before the next model call.
7. **Mark-Done** – `SP mark-done` – signals the task is complete; the agent should stop generating further work for this prompt. On next recall, the session loads with `status: done`.
8. **List Optimizers** – `SP optimizers` – list installed context/compaction skills (e.g., `strategic-compact`, `caveman`) that can be loaded once per session via `SP save --skill <name>`.

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

### Experience Learning
- `SP learn [--review]` – distills durable facts and lessons from the current session (repeated failures, fixes, repo conventions) into the per-project persistent store. With `--review`, scans recent turns for patterns worth keeping.
- Learned facts load automatically on the next `SP recall`, so mistakes are not repeated across sessions.
- Runs inline — no separate review model call.
- **Cost:** ~40 tokens per learning pass (estimate).

### Rate-Limit Model Fallback
- `SP fallback --chain "<model-1,model-2,…>"` – registers an ordered fallback chain. When a rate limit or usage limit error hits, the agent switches to the next model in the chain and retries the same step; checkpoint state (`SP save`) ensures no work is lost.
- **Disabled by default**; requires a host agent that can switch models mid-session. If the host cannot switch, report the limit and suggest resuming later instead.
- **Cost:** ~30 tokens to describe the chain; nothing when never triggered (estimate).

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
| Learning pass | +40 |
| Fallback chain setup | +30 |
| **Maximum** (all extras) | **~480** |

## Usage Example
```text
User: "Add a new API endpoint to fetch user stats."
SP budget --limit 300           # checks budget
SP recall --session 2023-projA  # restores state
SP find "api backend python"    # routes to your custom backend skill
SP index src/                   # optional: index source files for later queries
SP save --done "generated endpoint" --next "write tests"
```

## Lean Mode (always active)

These rules apply automatically — no command needed:

- Answer the question asked. No preamble, no restating the prompt, no recap of tool output. Quote only the lines that matter.
- Read files in targeted ranges; never re-read content already in context.
- Prefer one combined command over several small ones.
- For long sessions, if `SP optimizers` lists a context/compaction skill, load it **once per session**, not per message. Check at most once per session; record the result with `--skill`.

## Guardrails (always active)

- **Secrets & PII**: Never emit API keys, tokens, passwords, connection strings, or personally identifiable information. Redact automatically.
- **Scope discipline**: Do only what the user asked. Refuse scope creep. If a request expands, ask before acting.
- **No external calls without consent**: Never install packages, send data off-machine, or make network requests without explicit user approval.
- **Error transparency**: If a command fails (session not found, skill not installed, model limit hit), report the exact error and the next actionable step — never silently continue with wrong assumptions.

## Style Mirroring

Match the user's language, length, formality, formatting (bullets vs prose), and emoji use. Once the pattern is clear, persist it:

```text
SP save --done "<work done>" --next "<next step>" --style "casual, short bullets, no emoji"
```

Add `--global-style` to apply it across all future chats regardless of session:

```text
SP save --session <id> --done "<work done>" --next "<next step>" --global-style "formal, prose, mixed English-Bangla"
```

Update only when the user's style actually changes. On the next `SP recall`, the saved style loads automatically.

## Session Behavior

- **Fresh start**: `SP recall --create "my-project"` creates a clean session with no prior context.
- **Auto-create**: If `--session` is provided but doesn't exist, create it silently and proceed.
- **Fallback**: If no `--session` flag is given, use a project-scoped slug: `auto-<hash of cwd>`.
- **Completion marker**: When `SP mark-done` is used, the session stores `status: done`. On next `SP recall`, the agent sees this and knows the prior task finished.
- **Environment override**: `SESSION_PILOT_ID` in the environment forces a session ID when `--session` is omitted.

## Discovery Protocol (for agents that can scan the filesystem)

If the host agent has file access, it SHOULD scan these roots at startup and build an in-memory capability index:

```
~/.config/opencode/skills
~/.config/opencode/agent
~/.claude/skills
~/.claude/agents
~/.gemini/skills
~/.gemini/config/skills
~/.codex/skills
~/.cursor/skills
./.agents/skills
./.claude/skills
./.github/skills
```

`SP list` reads from this index. `SP find "<keywords>"` ranks entries by keyword overlap with `name` and `description` frontmatter fields. `SP optimizers` filters the index for skills whose description contains: `token`, `compress`, `compact`, `context budget`, `prompt optim`, `caveman`, `rtk`, `summariz`.

## When to Enable Optional Features
- **Semantic search** – large codebases where keyword routing misses relevant files.
- **Persistent store** – need to remember a flag (e.g., chosen framework) across sessions.
- **Unified memory** – multi-agent pipelines that share context.
- **Experience learning** – recurring projects where the same mistakes keep costing turns.
- **Model fallback** – metered plans or long sessions likely to hit rate/usage limits.
- All are **opt-in**: if you never call them, they never add tokens.

---