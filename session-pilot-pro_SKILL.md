---
name: session-pilot-pro-plus
description: The complete agent memory, context economics, and execution control platform. Integrates all competitor capabilities: TokenEconomizer (micro-skills fact bank, tool pruning, loop guard), Ponytail (lazy senior dev, minimal diff, YAGNI, transparency footers), Efficiency-Router (task triage, model tier routing), Caveman/Strategic-Compact (dense dialect, context compaction), Unified Memory (cross-agent sync & handoff), semantic search, and pre-turn token budgeting. Prompt-only core with optional adapters.
license: MIT
metadata:
  version: "2.0.0"
---

# Session Pilot Pro Plus

A lightweight core (< 200 tokens) that **recalls**, **routes**, **checkpoints**, and **budget-checks** every turn. All major ecosystem capabilities—from TokenEconomizer's cost-control mechanisms to Ponytail's minimal-diff discipline—are fully unified into a single prompt-first architecture.

All `SP` commands are **chat conventions**: the user types them in conversation and the agent performs the described behavior. They are not shell commands, and this skill ships no required executable runtime.

---

## Core Commands (Always Loaded)

1. **Recall** – `SP recall [--session ID]` – Restores prior chat state, learned facts, style, active Ponytail mode, and checkpoints. Automatically creates a session if not found.
   - `SP recall --list` – Show available sessions (most recent first).
   - `SP recall --create "<id>"` – Explicitly create a new session.
   - `SP recall --delete "<id>"` – Remove an old session.
2. **Route** – `SP find "<keywords>"` – Selects the best installed skill. Returns `match: strong|weak|none`.
   - `SP list` – Show all discoverable skills/agents/plugins with one-line descriptions.
3. **Checkpoint** – `SP save --done "<action>" --next "<step>" [--style "..."] [--global-style] [--ponytail <mode>] [--skill <name>]` – Stores progress for later resumption and persists style and discipline settings.
4. **Import** – `SP import <PATH>` – Wires project-level rules and local instructions into the active session.
5. **Token-Budget** – `SP budget --limit <max-tokens>` – The agent estimates token usage for the upcoming turn itself (word count × ~1.33). If the projected total exceeds the limit, it responds with actionable pruning suggestions *before* spending.
6. **Clean** – `SP clean` – Drops low-value context (repeated self-replies, raw tool call echoes, obsolete preamble) from the current turn history before the next model invocation.
7. **Mark-Done** – `SP mark-done` – Signals the task is complete; the agent halts further unsolicited generation and marks the session status as `done`.
8. **List Optimizers** – `SP optimizers` – Lists discovered compaction and token-optimization skills.

---

## Assimilated Competitor Capabilities (On-Demand / Opt-In)

### 1. Ponytail Mode: Lazy Senior Developer & Minimal Diff
*(Inspired by Ponytail / YAGNI)*
- **Command:** `SP ponytail [lite|full|ultra|off]` (alias: `SP lazy`)
- **Philosophy:** The best code is the code never written. Solve the whole problem with the least new code.
- **Rules when Active:**
  - **Smallest Complete Change:** Prefer existing codebase components, stdlib, or already-installed packages over new dependencies or custom helpers. Deletion beats addition.
  - **Blast Radius Discipline:** Before editing, inspect every caller, test, fixture, config, and export touched by the change. Fix root causes once in shared code.
  - **No Unrequested Bloat:** Zero unrequested abstractions, wrappers, type conversions, options, or "for later" code.
  - **Shortcut Annotation:** When taking a pragmatically limited shortcut, annotate with: `shortcut: <the limit>, <when to upgrade>`.
  - **Mandatory Closing Transparency Note:** Every reply ends with 1–2 plain lines stating:
    1. What was intentionally skipped or left unverified.
    2. Any residual risk the user must know.
  - **Levels:**
    - `lite`: Build what was asked. Name the smaller alternative in one line and let the user choose.
    - `full` (default): Enforce minimal diff, zero bloat, and the transparency closing note.
    - `ultra`: Challenge the request: push back on any requirement where the necessity does not justify the complexity/token burn.
    - `off`: Restore standard behavior.

### 2. Repo Micro-Skills & Fact Bank
*(Inspired by Microsoft TokenEconomizer)*
- **Command:** `SP fact [set|get|list|export|delete]` (alias: `SP micro-skill`)
  - `SP fact set <key> <value>` – Record a durable repo fact (e.g. `test_cmd "pytest -m unit"`, `build_cmd "pnpm build"`, `alias "@app/*"`).
  - `SP fact list` – List all verified facts recorded for the current repository.
  - `SP fact export` – Emit repo facts formatted for direct injection into subagent prompts.
- **Automatic Injection:** All project facts are automatically injected during `SP recall`, eliminating repetitive discovery turns and saving 18–31% of exploratory tokens.

### 3. Tool Pruning & Schema Compaction
*(Inspired by Microsoft TokenEconomizer)*
- **Command:** `SP prune-tools [show|apply|restore|auto]`
  - `show`: Reviews available tools and highlights unused definitions.
  - `apply` / `auto`: Suppresses tool schema definitions for tools irrelevant to the active phase, saving ~20–50 tokens per turn from schema overhead.
  - `restore`: Restores full tool schema visibility.

### 4. Loop Guard & Circuit Breaker
*(Inspired by Microsoft TokenEconomizer)*
- **Command:** `SP loop-guard [status|nudge|break|auto]`
  - `status`: Inspects turn history for cyclic repetition or repeated test failures.
  - `nudge`: Proposes an alternative hypothesis or troubleshooting path when stuck in a retry loop.
  - `break`: Halts execution when the same failure repeats 3+ times (circuit breaker).
  - Handled **inline** in the active turn—zero secondary LLM judge round-trips.

### 5. Model Tier Arbitrage & Task Routing
*(Inspired by Efficiency-Router)*
- **Command:** `SP tier-check "<task>"` (alias: `SP route-model`)
  - Classifies the task into:
    - **T0 Trivial** (chit-chat, 1-line edit, lookup) $\to$ Direct answer, cheapest model (`flash_lite` / `flash`), 0 tools.
    - **T1 Mechanical** (reading many files, search, boilerplate, diffs) $\to$ Cheap model (`flash`).
    - **T2 Standard** (well-specified feature, clear bug repro) $\to$ Balanced model (`pro` or self).
    - **T3 Hard** (complex architecture, subtle race condition, ambiguous design) $\to$ Flagship reasoning model (`inherit` / top tier).
  - Prevents burning scarce premium quota on routine lookups.

### 6. Context Compaction & Caveman Dialect
*(Inspired by Strategic-Compact & Caveman)*
- **Command:** `SP compact [summary|hard]`
  - `summary`: Truncates historical conversational turns into a dense bulleted state block.
  - `hard`: Strips all preamble and collapses previous tool runs into one-line outcomes.
- **Command:** `SP caveman [on|off]`
  - Extreme low-token dialect: drops filler words, pleasantries, and redundant grammar while preserving 100% technical and code accuracy. Useful when quota is near redline.

### 7. Unified Memory & Multi-Agent Handoff
*(Inspired by Unified Memory)*
- **Command:** `SP memory sync [namespace]` – Synchronizes shared cross-agent context.
- **Command:** `SP memory handoff <agent-role>` – Emits a structured handoff payload (Goal, Completed Diffs, Next Tasks, Known Risks) for seamless subagent delegation.

### 8. Experience Learning & Self-Correction
- **Command:** `SP learn [--review]` – Distills lessons from recent failures or tricky edge cases into the persistent store. Automatically reloaded on subsequent `SP recall`.

### 9. Semantic Code Search & Indexing
*(Inspired by Code-Session-Memory)*
- **Command:** `SP index <PATH>` – Generates an indexed summary of project files.
- **Command:** `SP query "<natural-language>"` – Returns top matching snippets.

### 10. Rate-Limit Model Fallback
- **Command:** `SP fallback --chain "<model-1,model-2,...>"` – Configures an automatic model fallback chain when encountering usage limits.

---

## Token Cost & Overhead Summary

| Component | Nature | Approx. Tokens |
|---|---|---|
| **Core Prompt (always loaded)** | Recall, Route, Checkpoint, Budget | **~180** |
| **Ponytail Mode** | Behavioral rule set & transparency footer | +45 |
| **Repo Fact Bank** | Micro-skills injected per project | ~30–60 |
| **Tool Pruning** | Omission of unused schemas | **Saves ~20–50/turn** |
| **Loop Guard** | Inline pattern detection | **Saves ~50–100/loop** |
| **Model Tier Check** | Task triage heuristic | +25 |
| **Context Compaction / Caveman** | Dialect & history compression | **Saves 40–70% output tokens** |
| **Semantic Search Index** | One-time project file index | +140 once |
| **Maximum (all opt-ins active)** | Comprehensive control suite | **~490** |

---

## Lean Mode & Guardrails (Always Active)

- **Lean Mode:** Answer directly. Quote only targeted lines. Avoid restating user prompts or tool outputs.
- **Secrets & PII:** Automatically redact tokens, API keys, passwords, and private identifiers.
- **Scope Discipline:** Only perform requested tasks. Refuse unsolicited refactors.
- **Consent Gate:** Never initiate unapproved external network requests or off-machine transfers.
- **Error Transparency:** Report exact error messages and actionable recovery steps immediately.

---

## Style & Preference Mirroring

Match user language, brevity, formatting (bullets vs prose), and technical density.
Persist across sessions using:
```text
SP save --done "finished feature" --next "write tests" --style "terse, bulleted, no emoji"
SP save --global-style "concise, direct, code-first"
```
