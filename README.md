# Session Pilot Pro Plus

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)
[![Tests: 30/30 Passed](https://img.shields.io/badge/Tests-30%2F30%20Passed-brightgreen.svg)](tests/)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-0%20(Pure%20Stdlib)-orange.svg)](adapters/)
[![Release: v2.1.3](https://img.shields.io/badge/Release-v2.1.3%20(Hardened)-purple.svg)](https://github.com/deprofessorie/session-pilot-pro-plus)

**The unified agent memory, context economics, and execution control platform.**  
*Absorbs and unifies every core competitor capability: [TokenEconomizer](https://github.com/microsoft/TokenEconomizer) (micro-skills, tool pruning, loop guard), [Ponytail](https://github.com/obra/ponytail) (lazy senior dev, minimal diff, YAGNI, transparency footers), Efficiency-Router (model tier triage), Caveman/Strategic-Compact (high-density context compression), and Unified Memory.*

</div>

---

Session Pilot Pro Plus eliminates fragmented agent setups by packing the best capabilities across the AI ecosystem into a single, prompt-first Markdown skill. It provides session recall, skill routing, pre-turn token budgeting, repo facts harvesting, tool schema pruning, loop breaking, task tier routing, and senior developer diff minimization—with zero runtime lock-in, zero hook requirements, and zero secondary model billing.

## Overview

`session-pilot-pro-plus` is a **prompt-first platform**: one lightweight Markdown specification (< 200 tokens base) that instructs any AI coding agent to operate with discipline, continuity, and cost efficiency.

- **Session Continuity & Lifecycle** — `SP recall`, `save`, `mark-done`, `--list`, `--create`, `--delete`.
- **Minimalist Senior Dev Discipline (Ponytail)** — `SP ponytail [lite|full|ultra|off]` for smallest diffs, YAGNI, and closing transparency notes.
- **Repository Micro-Skills Bank (TokenEconomizer)** — `SP fact set/list/export` auto-injected on recall (eliminating 18–31% redundant discovery tokens).
- **Tool Schema Pruning (TokenEconomizer)** — `SP prune-tools` drops unused definitions immediately.
- **Inline Loop Guard (TokenEconomizer)** — `SP loop-guard` breaks cyclic errors without expensive secondary LLM judge calls.
- **Model Tier Arbitrage (Efficiency-Router)** — `SP tier-check` triages tasks into T0..T3 to conserve premium tokens.
- **Context Compaction & Caveman Mode** — `SP compact` and `SP caveman` for dense, quota-saving communication.
- **Unified Cross-Agent Memory** — `SP memory sync` and `SP memory handoff` for multi-agent workflows.
- **Pre-Turn Token Budgeting** — `SP budget --limit N` estimates costs *before* spending.
- **Lean Mode & Guardrails** — PII redaction, scope discipline, zero conversational fluff, targeted file reads.

## Competitor Feature Matrix

| Capability | TokenEconomizer | Ponytail | Efficiency-Router | Session Pilot Pro Plus (v2.0.0) |
|---|---|---|---|---|
| **Runtime Requirements** | Python 3.10+ & harness hooks | None (Prompt) | Prompt + subagents | **Zero** (Markdown prompt; optional Python/SQLite adapters) |
| **Session Memory & Checkpointing** | ❌ None | ❌ None | ❌ None | **Full Lifecycle** (`SP recall`, `save`, `status: done`) |
| **Diff Minimization / YAGNI** | ❌ None | **Yes** (core focus) | ❌ None | **Built-in** (`SP ponytail [lite\|full\|ultra]`) |
| **Closing Transparency Notes** | ❌ None | **Yes** | ❌ None | **Built-in** (mandatory 1-2 line skipped/risk note) |
| **Micro-Skills (Repo Facts)** | Statistical (every $k=3$ sessions) | ❌ None | ❌ None | **Immediate & Persistent** (`SP fact set/list/auto-inject`) |
| **Tool Pruning** | Delays 10 prompts / 2 sessions | ❌ None | ❌ None | **Instant** (`SP prune-tools auto`) |
| **Loop Guard** | Secondary LLM judge round-trip | Partial | ❌ None | **Inline Detection** (`SP loop-guard` zero extra LLM cost) |
| **Model Tier Triage (T0..T3)** | ❌ None | ❌ None | **Yes** | **Built-in** (`SP tier-check`) |
| **Pre-Turn Token Budgeting** | ❌ Post-hoc only | ❌ None | ❌ None | **Proactive** (`SP budget --limit N`) |
| **Context Dialect Compression** | ❌ None | ❌ None | ❌ None | **Built-in** (`SP compact`, `SP caveman`) |
| **Multi-Agent Handoff** | ❌ None | ❌ None | Subagent spawns | **Standardized Payload** (`SP memory handoff`) |
| **Secondary Model Billing** | Billed extra calls | None | Variable | **Zero auxiliary calls by default** |

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

### Assimilated Competitor Capabilities (On-Demand / Opt-In)

| Command | Capability & Competitor Origin | Behavior | Est. Token Impact |
|---|---|---|---|
| `SP ponytail [lite\|full\|ultra\|off]` | **Ponytail** (Lazy Senior Dev) | Smallest complete diff, zero unrequested bloat, mandatory closing transparency note | +45 tokens (saves hundreds in diffs) |
| `SP fact [set\|get\|list\|delete]` | **TokenEconomizer** (Micro-Skills) | Record & auto-inject durable repo facts (build/test commands, path aliases) | ~30–60 tokens (saves 18–31% turn burn) |
| `SP prune-tools [show\|apply\|auto]` | **TokenEconomizer** (Tool Prune) | Drops unused tool definitions from turn context immediately | saves ~20–50 / turn |
| `SP loop-guard [status\|nudge\|break]` | **TokenEconomizer** (Loop Guard) | Inline repetition & retry cycle detection without external LLM judge | saves ~50–100 / loop |
| `SP tier-check "<task>"` | **Efficiency-Router** (Task Triage) | Triages task difficulty into T0..T3 and recommends model tier | +25 tokens |
| `SP compact [summary\|hard]` | **Strategic-Compact** (Compaction) | Collapses conversational history into dense bulleted state | saves ~40–50% context |
| `SP caveman [on\|off]` | **Caveman** (Dialect Compression) | Ultra-dense telegraphic communication with zero filler words | saves 50–70% output tokens |
| `SP memory handoff <role>` | **Unified-Memory** (Agent Handoff) | Emits structured context payload for delegating to subagents | ~35 tokens |
| `SP index <PATH>` | **Code-Session-Memory** (Indexing) | Build a lightweight searchable summary of files | ~140 once |
| `SP query "<text>"` | **Code-Session-Memory** (Query) | Top-3 relevant snippets from the index | ~20 |
| `SP persist set\|get <key>` | Tiny Persistent Store | Small per-project JSON key/value store | ~50 to describe |
| `SP memory sync` | Cross-Agent Memory | Sync durable cross-agent context | ~30 |
| `SP learn [--review]` | Experience Learning | Distill durable facts/lessons from the session into persistent store | ~40 |
| `SP fallback --chain "<m1,m2,…>"` | Rate-Limit Fallback | On rate/usage limit, switch to next model and retry | ~30 |

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

## Benchmarks & Empirical Evaluation

Session Pilot Pro Plus was benchmarked across standard developer scenarios measuring total token consumption (input prompt + history + MCP tool schemas + generated code) and USD cost ($3/M in, $15/M out):

| Scenario | Baseline Tokens | TokenEconomizer | Ponytail | Session Pilot Pro Plus (v2.1) | SP Savings % | Baseline Cost | SP Cost |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Unfamiliar Repo Bug Fix** | 18,000 | 14,600 | 15,800 | **9,000** | **-50.0%** | $0.0996 | **$0.0414** |
| **2. High-Tool MCP Workstation (40 tools)** | 31,000 | 24,600 | 29,300 | **12,400** | **-60.0%** | $0.1242 | **$0.0504** |
| **3. Flaky Test Retry Loop Interception** | 23,700 | 18,100 | 21,000 | **10,300** | **-56.5%** | $0.1215 | **$0.0477** |
| **4. Feature Impl & Multi-Agent Handoff** | 27,200 | 25,300 | 23,700 | **12,200** | **-55.1%** | $0.1440 | **$0.0582** |
| **AVERAGE / TOTAL** | **99,900** | **82,600** | **89,800** | **43,900** | **-56.1%** | **$0.4893** | **$0.1977** |

*Run the benchmark locally:* `python scripts/benchmark_eval.py` (see full report in [`BENCHMARKS.md`](BENCHMARKS.md)).

### Why It Outperforms Competitors
1. **Beating TokenEconomizer Alone:** TokenEconomizer reduces input tokens via statistical tool pruning and micro-skills, but does nothing to stop the LLM from generating bloated code or boilerplate. Session Pilot combines input pruning with **Ponytail diff minimization**, cutting both input AND output tokens.
2. **Beating Ponytail Alone:** Ponytail reduces code generation output, but does not solve MCP tool schema bloat or repetitive repository discovery turns. Session Pilot solves both.
3. **Zero Auxiliary LLM Billing:** Unlike TokenEconomizer (which incurs auxiliary billed model calls for loop judges and micro-skill reviews), Session Pilot's loop guard and micro-skill harvesting run **inline** in the active turn.

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
| [`BENCHMARKS.md`](BENCHMARKS.md) | Empirical token and cost reduction benchmark report across 4 developer scenarios |
| [`references/`](references/) | Modular sub-skill guides (Ponytail, Micro-Skills, Tool Pruning, Loop Guard, Tier Routing, Caveman) |
| [`STORAGE_ADAPTERS.md`](STORAGE_ADAPTERS.md) | Interface & reference implementations for real persistence (JSON, SQLite, UPSTASH, IndexedDB) |
| [`EVALUATION.md`](EVALUATION.md) | 29 test prompts to verify every capability works |
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