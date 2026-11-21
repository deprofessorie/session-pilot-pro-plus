# Session Pilot Pro Plus

**Token-aware session memory, skill routing, and context economy — a prompt-only rival to [TokenEconomizer](https://github.com/microsoft/TokenEconomizer).**

Session Pilot Pro Plus delivers every core mechanism TokenEconomizer offers — **micro-skills, tool pruning, and loop guard** — plus session recall, skill routing, pre-turn token budgeting, experience learning, rate-limit model fallback, semantic search, and cross-agent memory. It ships as a single Markdown skill: no Python runtime, no plugin hooks, no side model calls. By design it is faster to act and cheaper to run, because everything happens inline in the agent you already use.

## Overview

`session-pilot-pro-plus` is a **prompt-only skill**: one Markdown file that instructs an AI coding agent to recall session state, route requests to the best available skill, checkpoint progress, and keep token usage under control. There is no runtime code, CLI binary, or external dependency.

- Per-chat memory recall & checkpointing with session lifecycle (create, list, delete).
- Smart routing to the best installed skill/agent with `SP list` discovery.
- Pre-turn token-budget checks to avoid cost overruns.
- Opt-in helpers that prune unused tool calls and break repetitive loops.
- Experience learning: durable facts and lessons distilled from failures and fixes.
- Automatic model fallback when a rate limit or usage limit is hit.
- Optional semantic search, persistent key/value store, and cross-agent memory sync.
- **Lean mode** — automatic verbosity reduction on every turn.
- **Style mirroring** — adapts to your communication patterns and persists them.
- **Guardrails** — secrets/PII redaction, scope discipline, consent gates, error transparency.
- **Session lifecycle** — fresh start, auto-create, completion markers, env override.
- **Discovery protocol** — scans standard skill directories for installed capabilities.

## How it compares to TokenEconomizer

[TokenEconomizer](https://github.com/microsoft/TokenEconomizer) (Microsoft) is an experience-driven plugin. It requires **Python 3.10+**, a per-agent plugin installation, and hook integration. Its mechanisms gather evidence over time and make **their own model calls** (micro-skill reviews, a loop-guard judge) billed through your agent login. Its published results: 18.4–30.9% lower mean cost on SWE-Bench, 16–21% on Web-Bench.

Session Pilot Pro Plus covers the same three mechanisms and adds six more capabilities, with zero installation overhead:

### Feature parity

| Capability | TokenEconomizer | Session Pilot Pro Plus |
|---|---|---|
| **Micro-skills** (repo facts/helpers) | Learned from failures/model reviews every *k* = 3 sessions | `SP micro-skill <name>` on demand; facts captured inline via `SP save` — no review model call |
| **Tool pruning** | Removes tools after *p* = 10 prompts across *m* = 2 sessions of evidence | `SP prune-tools` — immediate, on demand, no evidence-gathering wait |
| **Loop guard** | LLM judge detects stuck turns (confidence ≥ 0.7, up to 1 redirect) | `SP loop-guard` — the main agent detects repetition patterns directly; no judge round-trip |
| **Experience learning** | Facts learned from failures/model reviews every *k* = 3 sessions | `SP learn` — lessons distilled inline at checkpoints, persisted, and auto-loaded on `SP recall`; no review model call |
| **Rate-limit model fallback** | — | `SP fallback --chain "<models>"` — switches to the next model and retries when a rate/usage limit hits |
| **Session recall / resume** | — | `SP recall [--session ID]` with `--list`, `--create`, `--delete` |
| **Checkpointing** | — | `SP save --done … --next …` with `--style`, `--global-style`, `--skill` |
| **Skill routing** | — | `SP find "<keywords>"` with `match: strong\|weak\|none` + `SP list` |
| **Pre-turn token budget** | — (savings measured after the fact) | `SP budget --limit N` estimates cost *before* the turn runs |
| **Semantic search** | — | `SP index <PATH>` / `SP query "<text>"` |
| **Persistent store** | Plugin state in `~/.tokeneconomizer` | `SP persist set\|get` — small per-project JSON values |
| **Cross-agent memory** | Each agent learns on its own | `SP memory sync` — shared durable context |
| **Secondary model calls** | Implicit (judge/review calls always possible) | `SP call-model <model>` — explicit, **disabled by default** |
| **Context cleaning** | — | `SP clean` — drops low-value history before next turn |
| **Task completion signal** | — | `SP mark-done` — stops generation, marks session `done` |
| **Lean mode** | — | Built-in: no preamble, targeted reads, combined commands |
| **Style mirroring** | — | Auto-detect + persist with `--style` / `--global-style` |
| **Guardrails** | — | Secrets/PII, scope discipline, consent, error transparency |

### Why it is faster and lighter (by design)

1. **No runtime, no hooks.** TokenEconomizer runs Python hooks on sessions and prompt turns. Session Pilot Pro Plus is text the agent reads once — there is no process to start, no hook latency, no install/update cycle (`git pull` + re-add plugin).
2. **No side model calls.** TokenEconomizer's loop-guard judge and micro-skill reviews are extra LLM round-trips that cost tokens and add latency. Every Session Pilot helper runs inline in the current turn — a loop-guard check costs ~50 tokens of context, not a second model call.
3. **Opt-in, not always-on.** TokenEconomizer's mechanisms continuously gather evidence. Session Pilot's core prompt is ~180 tokens; each helper adds tokens **only when invoked** (~20–50 per call).
4. **Immediate effect.** Pruning and loop-breaking happen the moment you ask — no waiting for 10 prompts or 3 sessions of evidence.
5. **Budget before spend.** `SP budget` estimates the upcoming turn's cost up front, so you can prune *before* overrunning, not after.

> All token figures below are **design estimates** (≈ 1.33 tokens per word), not measured benchmarks. See [Benchmarks & methodology](#benchmarks--methodology).

## Installation

No dependencies, nothing to build, no marketplace commands.

1. Copy `session-pilot-pro_SKILL.md` into your agent's skills directory (rename to `SKILL.md` inside a `session-pilot-pro-plus` folder if your harness expects that layout), **or**
2. Paste its contents into your agent's persistent instructions.

Works with any harness that reads Markdown skills or custom instructions — OpenCode, Qoder, Claude Code, Codex CLI, Cursor, Gemini CLI, Antigravity, and similar agents. No per-agent plugin variants, no Python version requirements.

## Quick start

```text
SP recall --session my-project     # restore prior state (or start fresh)
SP budget --limit 300              # cap this turn's estimated cost
SP find "api backend python"       # route to the best installed skill
SP save --done "scaffolded API" --next "write tests"
```

All commands are **chat conventions**: type them in the conversation and the agent performs the behavior. They are not shell commands.

## Command reference

### Core (always loaded, ~180 tokens total)

| Command | Behavior |
|---|---|
| `SP recall [--session ID]` | Restore prior chat state or start a fresh session |
| `SP recall --list` | Show available sessions (most recent first) |
| `SP recall --create "<id>"` | Explicitly create a new session |
| `SP recall --delete "<id>"` | Remove an old session |
| `SP find "<keywords>"` | Select the best installed skill; returns `match: strong\|weak\|none` |
| `SP list` | Show all discoverable skills/agents/plugins with one-line descriptions |
| `SP save --done "<action>" --next "<step>" [--style "..."] [--global-style] [--skill <name>]` | Checkpoint progress for later resumption; persists style preferences when provided |
| `SP import <PATH>` | Wire project-level rules into the session |
| `SP budget --limit <max>` | Estimate the upcoming turn's tokens; suggest pruning if over limit |
| `SP clean` | Drop low-value context (repeated self-replies, tool call echoes, old preamble) from the current turn's history |
| `SP mark-done` | Signal the task is complete; agent stops generating further work; session loads with `status: done` on next recall |
| `SP optimizers` | List installed context/compaction skills (e.g., `strategic-compact`, `caveman`) |

### Opt-in helpers (loaded only when invoked)

| Command | Behavior | Est. added tokens |
|---|---|---|
| `SP micro-skill <name>` | One focused helper action (quick lint, dependency check, …) | ~30 |
| `SP prune-tools` | Drop unused tool calls from the turn context | saves ~20–40 |
| `SP loop-guard` | Detect repetitive patterns; suggest a break | saves ~50–80 |
| `SP call-model <model>` | Secondary LLM call, if the host supports it (off by default) | variable |
| `SP index <PATH>` | Build a lightweight searchable summary of files | ~140 once |
| `SP query "<text>"` | Top-3 relevant snippets from the index | ~20 |
| `SP persist set\|get <key>` | Small per-project JSON key/value store | ~50 to describe |
| `SP memory sync` | Sync durable cross-agent context | ~30 |
| `SP learn [--review]` | Distill durable facts/lessons from the session into the persistent store; loaded on next `SP recall` | ~40 |
| `SP fallback --chain "<m1,m2,…>"` | On rate/usage limit, switch to the next model and retry (host support required; off by default) | ~30 |

## Real-world use cases

### 1. Resuming a week-old feature branch
**Scenario:** You return to a project after days away; the agent has no memory of where you stopped.
```text
SP recall --session payments-api
SP save --done "webhook signature verification" --next "add retry queue"
```
The agent restores the checkpoint (done/next state, decisions, conventions) and continues exactly where you left off. TokenEconomizer has no session-resume concept — its learned facts persist, but your *task state* does not.
**Cost:** core prompt only (~180 tokens); no review model call.

### 2. Taming a 50-tool MCP setup
**Scenario:** Your agent loads dozens of MCP tools; every definition is sent with every request, but you only use five of them today.
```text
SP prune-tools
```
Unused tool definitions are dropped from the turn context immediately. TokenEconomizer needs ~10 prompts across 2 sessions of evidence before it prunes — and pruning is unavailable entirely on several agents (Pi, Cursor, Grok, opencode, Hermes, Antigravity, Droid). Session Pilot's prune is a context instruction, so it works anywhere the skill loads.
**Savings:** ~20–40 tokens per turn, from the first turn.

### 3. Hard cost cap on a long session
**Scenario:** You're on a metered plan and want no turn to exceed ~300 tokens of overhead.
```text
SP budget --limit 300
```
Before acting, the agent estimates the prompt + context + loaded helpers (words × ~1.33). Over budget? It returns concrete suggestions — trim recall history, disable a helper, summarize a large file — *before* spending. TokenEconomizer reports savings after the fact; it cannot gate a turn pre-emptively.
**Cost:** ~30 tokens for the check itself.

### 4. Breaking a retry loop without a judge call
**Scenario:** The agent keeps re-running the same failing test with the same fix attempt.
```text
SP loop-guard
```
The agent inspects its own recent turns for repetition and proposes a different strategy. TokenEconomizer achieves this with an **LLM judge** (confidence threshold 0.7) — an extra model round-trip per check, billed to your login, and it never stops the turn itself. Session Pilot's guard is inline pattern detection: no second call, no added latency.
**Savings:** ~50–80 tokens of duplicated work, plus the judge call you never make.

### 5. Finding code in an unfamiliar repository
**Scenario:** A large codebase; keyword routing misses the relevant files.
```text
SP index src/
SP query "where is the retry backoff computed"
SP find "backend python"
```
Index once (~140 tokens), then each query costs ~20 tokens and returns the top-3 snippets. Routing then picks the best installed skill for the actual work. TokenEconomizer offers no search or routing — it optimizes cost, not navigation.

### 6. Multi-agent handoff
**Scenario:** One agent scaffolds a feature; another writes tests; a third reviews.
```text
SP memory sync
SP persist set framework "fastapi"
```
Durable context and small project flags survive across agents and sessions. TokenEconomizer explicitly learns *per agent* — each agent re-learns facts on its own. Session Pilot shares them.
**Cost:** ~30 tokens per sync; ~50 to describe the store.

### 7. Learning from repeated failures
**Scenario:** The agent keeps tripping over the same repo quirk (e.g., tests require a local Redis, imports use a custom alias).
```text
SP learn --review
SP save --done "fixed import alias" --next "run full suite"
```
The agent distills the lesson into a durable fact ("tests need Redis on :6379", "use `@app/` alias, never relative imports") and stores it per project. On the next `SP recall`, learned facts load automatically — the mistake is never repeated. TokenEconomizer learns too, but via periodic **model reviews** (extra billed calls every 3 sessions); Session Pilot learns inline, at the moment the lesson occurs, for ~40 tokens.
**Cost:** ~40 tokens per learning pass; facts load with the core recall.

### 8. Surviving a rate limit mid-task
**Scenario:** Halfway through a refactor, the primary model returns a rate-limit or usage-cap error.
```text
SP fallback --chain "primary-model,fast-model,local-model"
```
When a limit hits, the agent switches to the next model in the chain and retries the same step — the checkpoint (`SP save`) means no work is lost. TokenEconomizer has no fallback: a capped model stalls the session. Fallback is **off by default** and requires a host agent that can switch models mid-session.
**Cost:** ~30 tokens to describe the chain; nothing when never triggered.

## Token-budget mechanics

- **Agent-side estimate** — no tokenizer library, no external tooling, no model call. The agent counts words in the upcoming prompt, accumulated context, and loaded helper descriptors, and multiplies by ~1.33.
- If `estimated_total > limit`:
  ```
  [!] Token budget exceeded (estimated X > limit Y). Suggested actions:
   - Trim recall history (`SP save --prune`)
   - Disable optional sub-skill(s) (`SP disable <name>`)
   - Summarize large chunks (`SP summarize <path>`)
  ```
- Raise the limit with `SP budget --limit <new>` or accept a suggestion. Estimates vary by model and tokenizer.

## Token cost summary (design estimates)

| Component | Approx. tokens |
|---|---|
| Core prompt | ~180 |
| Budget check | +30 |
| Semantic index (once) | +140 |
| Persistent store init | +50 |
| Learning pass | +40 |
| Fallback chain setup | +30 |
| **Maximum, all extras loaded** | **~480** |

Typical turns use the core plus one or two helpers: **~200–260 tokens**, versus always-on evidence gathering plus judge/review model calls in a plugin-based approach.

## Benchmarks & methodology

TokenEconomizer publishes measured results (18.4–30.9% lower mean cost on SWE-Bench across five agent-model combinations; cheaper in all 30 tested cells). **Session Pilot Pro Plus figures in this document are architectural design estimates, not measured benchmarks.** The speed and token advantages follow from structure — no runtime, no side model calls, opt-in loading — and hold by construction wherever the skill loads. Controlled SWE-Bench-style comparisons are welcome as community contributions; until then, treat numeric comparisons as estimates.

## Status & limitations

- Prompt-only: behavior depends on the host agent following the instructions. No executables or test suite ship in this repo.
- Token estimates are approximate and vary by model/tokenizer.
- Optional features (secondary model calls, indexing, model fallback) depend on host-agent capabilities; fallback needs a host that can switch models mid-session.
- Learning is agent-driven (`SP learn` at checkpoints), not hook-triggered — facts are captured when you checkpoint or ask, and loaded automatically on recall.

## Contributing

- Fork the repository and create a feature branch (`git checkout -b my-feature`).
- Keep the core prompt small; document the token impact of any new helper.
- Benchmark contributions (measured token/cost comparisons) are especially welcome.
- Open a Pull Request with a clear description.

## Documentation

| File | Purpose |
|---|---|
| [`STORAGE_ADAPTERS.md`](STORAGE_ADAPTERS.md) | Interface & reference implementations for real persistence (JSON, SQLite, UPSTASH, IndexedDB) |
| [`EVALUATION.md`](EVALUATION.md) | 25 test prompts to verify every capability works |
| [`COMPATIBILITY.md`](COMPATIBILITY.md) | Agent support matrix — which commands work on OpenCode, Claude Code, Codex, Cursor, web agents, etc. |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | How to add adapters, features, or docs the right way |

## Verification & CI

Run the full suite locally before submitting anything:

```bash
python scripts/verify.py --adapter json_file
python scripts/verify.py --adapter sqlite
python scripts/repl.py                  # interactive smoke-test
docker build -t sp-test . && docker run --rm sp-test python scripts/verify.py
```

GitHub Actions runs automatically on every push/PR: verifies both adapters, builds the Docker image, and validates documentation.

## Demo REPL

A standalone interactive shell for testing every command without an LLM harness:

```bash
python scripts/repl.py --adapter json_file --home /tmp/sp-demo
# Then type: SP recall --create demo  →  SP save --done x --next y  →  SP list  →  SP exit
```

## License

MIT © 2026 deProfessori (declared in the skill frontmatter).