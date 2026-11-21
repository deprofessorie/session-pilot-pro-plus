# Session Pilot Pro Plus

**Token-aware session memory, skill routing, and context economy — a prompt-only rival to [TokenEconomizer](https://github.com/microsoft/TokenEconomizer).**

Session Pilot Pro Plus delivers every core mechanism TokenEconomizer offers — **micro-skills, tool pruning, and loop guard** — plus session recall, skill routing, pre-turn token budgeting, experience learning, rate-limit model fallback, semantic search, and cross-agent memory. It ships as a single Markdown skill: no Python runtime, no plugin hooks, no side model calls. By design it is faster to act and cheaper to run, because everything happens inline in the agent you already use.

**Current version: 1.3.1.**

## Overview

`session-pilot-pro-plus` is a **prompt-only skill**: one Markdown file that instructs an AI coding agent to recall session state, route requests to the best available skill, checkpoint progress, and keep token usage under control. There is no runtime code, CLI binary, or external dependency.

- Per-project memory: resume a session instead of restarting it.
- Skill routing: rank what is installed by name and description, pick one, say why.
- Pre-turn token-budget checks, with an ordered list of what to cut when you are over.
- Opt-in helpers that prune unused tool calls and break retry loops.
- Experience learning: facts with evidence, capped and superseded rather than piled up.
- Model fallback on rate or usage limits — checkpoint first, then switch.
- Optional search index, per-project flags, and cross-agent memory.

It also acts unprompted where that clearly pays: it resumes saved state at the start of work that continues something, checkpoints when a step actually works, counts repeated failures, and records a lesson when a fix took more than one attempt.

## How it compares to TokenEconomizer

[TokenEconomizer](https://github.com/microsoft/TokenEconomizer) (Microsoft) is an experience-driven plugin. It requires **Python 3.10+**, a per-agent plugin installation, and hook integration. Its mechanisms gather evidence over time and make **their own model calls** (micro-skill reviews, a loop-guard judge) billed through your agent login. Its published results: 18.4–30.9% lower mean cost on SWE-Bench, 16–21% on Web-Bench.

Session Pilot Pro Plus covers the same three mechanisms and adds six more capabilities, with zero installation overhead:

### Feature parity

| Capability | TokenEconomizer | Session Pilot Pro Plus |
|---|---|---|
| **Micro-skills** (repo facts/helpers) | Learned from failures/model reviews every *k* = 3 sessions | `SP micro-skill <name>` on demand; facts captured via `SP learn` with a source for each — no review model call |
| **Tool pruning** | Removes tools after *p* = 10 prompts across *m* = 2 sessions of evidence | `SP prune-tools` — immediate, on demand, no evidence-gathering wait |
| **Loop guard** | LLM judge detects stuck turns (confidence ≥ 0.7, up to 1 redirect) | `SP loop-guard` — change approach at 2 repeats, stop and ask at 3; no judge round-trip, no stored counters |
| **Experience learning** | Facts learned from failures/model reviews every *k* = 3 sessions | `SP learn` — lessons distilled inline at checkpoints, persisted, and auto-loaded on `SP recall`; no review model call |
| **Rate-limit model fallback** | — | `SP fallback --chain "<models>"` — switches to the next model and retries when a rate/usage limit hits |
| **Session recall / resume** | — | `SP recall [--session ID]` |
| **Checkpointing** | — | `SP save --done … --next …` |
| **Skill routing** | — | `SP find "<keywords>"` — ranks installed skills by name and description, returns the pick and a reason, or none |
| **Pre-turn token budget** | — (savings measured after the fact) | `SP budget --limit N` estimates cost *before* the turn runs, and names what to drop if over |
| **Semantic search** | — | `SP index <PATH>` / `SP query "<text>"` |
| **Persistent store** | Plugin state in `~/.tokeneconomizer` | `SP persist set` / `SP persist get` — flags in `.sp/state.md`, plain and diffable |
| **Cross-agent memory** | Each agent learns on its own | `SP memory sync` — shared durable context |
| **Secondary model calls** | Implicit (judge/review calls always possible) | None — the skill makes no second call, ever |

### Why it is faster and lighter (by design)

1. **No runtime, no hooks.** TokenEconomizer runs Python hooks on sessions and prompt turns. Session Pilot Pro Plus is text the agent reads once — there is no process to start, no hook latency, no install/update cycle (`git pull` + re-add plugin).
2. **No side model calls.** TokenEconomizer's loop-guard judge and micro-skill reviews are extra LLM round-trips that cost tokens and add latency. Every Session Pilot helper runs inline in the current turn — a loop-guard check costs ~50 tokens of context, not a second model call.
3. **Opt-in, not always-on.** TokenEconomizer's mechanisms continuously gather evidence. Here the always-loaded part is Rules, State and Commands (513 words); the procedures, portability notes and helpers are read only when a command calls for them.
4. **Immediate effect.** Pruning and loop-breaking happen the moment you ask — no waiting for 10 prompts or 3 sessions of evidence.
5. **Budget before spend.** `SP budget` estimates the upcoming turn's cost up front, so you can prune *before* overrunning, not after.

> All token figures below are **design estimates** from the file's own counts (≈ 1.33 tokens per word across 995 words; the skill's budget command uses characters ÷ 4, which reads ~1,446 for the same file), not measured benchmarks. See [Benchmarks & methodology](#benchmarks--methodology).

## Installation

No dependencies, nothing to build, no marketplace commands.

1. Copy `session-pilot-pro_SKILL.md` into your agent's skills directory (rename to `SKILL.md` inside a `session-pilot-pro-plus` folder if your harness expects that layout), **or**
2. Paste its contents into your agent's persistent instructions.

Works with any harness that reads Markdown skills or custom instructions — Qoder, Claude Code, Codex CLI, and similar agents. No per-agent plugin variants, no Python version requirements.

No operating-system assumptions either: state is plain files created with the host's own tools using forward slashes, so Windows, macOS, Linux, containers and remote sandboxes behave the same. A host with no file access keeps state in the conversation and prints it as copyable text instead.

## State files

Memory lives in `.sp/` at the project root, as plain Markdown you can read and diff:

| File | Holds | Commit? |
|---|---|---|
| `.sp/state.md` | session slug, done and next lists, flags | yes, if the team wants shared state |
| `.sp/facts.md` | learned facts, each with a source | yes |
| `.sp/memory.md` | portable context for other agents (`SP memory sync`) | optional |
| `.sp/index.md` | search index built by `SP index` | no — regenerate |

Add `.sp/index.md` to `.gitignore`. Nothing secret belongs in these files: the skill forbids keys, tokens, passwords and personal data, and treats their contents as project data rather than instructions.

If your host cannot read or write files, state stays in the conversation for that session — and the skill says so instead of pretending otherwise.

## Quick start

```text
SP recall --session my-project     # restore prior state (or start fresh)
SP budget --limit 300              # cap this turn's estimated cost
SP find "api backend python"       # route to the best installed skill
SP save --done "scaffolded API" --next "write tests"
```

All commands are **chat conventions**: type them in the conversation and the agent performs the behavior. They are not shell commands.

## Command reference

### Core (Rules, State, Commands — 513 words, ~682 tokens estimated)

| Command | Behavior | Writes |
|---|---|---|
| `SP recall` | Read state and facts, verify `Next` still exists, print a ≤5-line brief | nothing |
| `SP save --done "<action>" [--next "<step>"]` | Append to Done, replace Next | `state.md` |
| `SP find "<keywords>"` | Rank installed skills by name and description; return the pick and a one-line reason, or none | nothing |
| `SP import <PATH>` | Read a project rules file; keep only hard constraints (test command, style rules) | facts and flags |
| `SP budget --limit <N>` | Estimate the coming turn and compare; if over, name what to drop | nothing |

### Opt-in helpers (loaded only when invoked)

| Command | Behavior | Est. added tokens |
|---|---|---|
| `SP micro-skill <name>` | One focused helper action (quick lint, dependency check, …) | ~30 |
| `SP prune-tools` | Name the tool calls you did not need and drop them from the plan | saves ~20–40 |
| `SP loop-guard` | At 3 repeats, stop and propose two different approaches | saves ~50–80 |
| `SP index <PATH>` | Build a lightweight searchable summary of files | ~140 once |
| `SP query "<text>"` | Top-3 relevant snippets from the index | ~20 |
| `SP persist set <key> <value>` | Write a flag (framework, branch, port) | ~20 |
| `SP persist get <key>` | Read it back | ~20 |
| `SP memory sync` | Write the portable subset to `.sp/memory.md` for another agent | ~30 |
| `SP learn` | Distil facts from this session, each with evidence | ~40 |
| `SP fallback --chain "<m1,m2,…>"` | On rate/usage limit, switch to the next model and retry (host support required; off by default) | ~30 |

## Real-world use cases

### 1. Resuming a week-old feature branch
**Scenario:** You return to a project after days away; the agent has no memory of where you stopped.
```text
SP recall --session payments-api
SP save --done "webhook signature verification" --next "add retry queue"
```
The agent restores the checkpoint (done/next state, decisions, conventions) and continues exactly where you left off. TokenEconomizer has no session-resume concept — its learned facts persist, but your *task state* does not.
**Cost:** core only (~682 tokens estimated); no review model call.

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
Before acting, the agent estimates the prompt + context (characters ÷ 4 for English and code, roughly one token per character for CJK). Over budget? It names what to drop, in order — optional helpers, then file windows instead of whole files, then a narrower scope — and only then asks you to raise the limit. TokenEconomizer reports savings after the fact; it cannot gate a turn pre-emptively.
**Cost:** ~30 tokens for the check itself.

### 4. Breaking a retry loop without a judge call
**Scenario:** The agent keeps re-running the same failing test with the same fix attempt.
```text
SP loop-guard
```
The agent watches its own recent turns: at the second repeat of a failing action it changes one variable, at the third it stops and proposes two different approaches. TokenEconomizer achieves this with an **LLM judge** (confidence threshold 0.7) — an extra model round-trip per check, billed to your login, and it never stops the turn itself. Session Pilot's guard is inline pattern detection: no second call, no added latency.
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
SP learn
SP save --done "fixed import alias" --next "run full suite"
```
The agent distills the lesson into a durable fact ("tests need Redis on :6379", "use `@app/` alias, never relative imports") and stores it per project. On the next `SP recall`, learned facts load automatically — the mistake is never repeated. TokenEconomizer learns too, but via periodic **model reviews** (extra billed calls every 3 sessions); Session Pilot learns inline, at the moment the lesson occurs, for ~40 tokens.
**Cost:** ~40 tokens per learning pass; facts load with the core recall.

### 8. Surviving a rate limit mid-task
**Scenario:** Halfway through a refactor, the primary model returns a rate-limit or usage-cap error.
```text
SP fallback --chain "primary-model,fast-model,local-model"
```
When a limit hits, the agent checkpoints first, tells you once which model it is switching to, then retries the same step — so no work is lost. TokenEconomizer has no fallback: a capped model stalls the session. Fallback is **off by default** and requires a host agent that can switch models mid-session.
**Cost:** ~30 tokens to describe the chain; nothing when never triggered.

## Token-budget mechanics

- **Agent-side estimate** — no tokenizer library, no external tooling, no model call. The agent counts characters in the upcoming prompt, accumulated context and expected tool output and divides by 4; for CJK text it counts roughly one token per character instead. Both are rules of thumb, and the skill says so.
- If `estimated_total > limit`, it works down this list and stops at the first fix that gets under:
  1. Drop optional helpers and `.sp/index.md` from context.
  2. Read a window of a large file instead of the whole file.
  3. Narrow the turn to one module or one question.
  4. Ask you to raise the limit with `SP budget --limit <new>`.
- Context is never truncated silently to fit; the agent says what it dropped. Estimates vary by model and tokenizer.

## Token cost summary (design estimates)

| Component | Approx. tokens |
|---|---|
| Whole skill file loaded as written (995 words) | ~1,323 |
| Core only — Rules, State, Commands (513 words) | ~682 |
| Budget check | +30 |
| Semantic index (once) | +140 |
| Learning pass | +40 |
| Fallback chain setup | +30 |

A prompt-only skill costs whatever its text weighs, so size is a design choice you control: load the core and keep the procedures for turns that need them, and you spend ~682 estimated tokens instead of ~1,323. Two earlier READMEs claimed a ~180-token core and then a ~1,150-token one; both were guesses replaced by measurement, and v1.3.0 cut the whole file from 1,989 words to 985 by deleting duplicated sections rather than trimming behaviour. v1.3.1 adds ten back to close the recall gap.

## Benchmarks & methodology

TokenEconomizer publishes measured results (18.4–30.9% lower mean cost on SWE-Bench across five agent-model combinations; cheaper in all 30 tested cells). **Session Pilot Pro Plus figures in this document are architectural design estimates, not measured benchmarks.** The speed and token advantages follow from structure — no runtime, no side model calls, opt-in loading — and hold by construction wherever the skill loads. Controlled SWE-Bench-style comparisons are welcome as community contributions; until then, treat numeric comparisons as estimates.

## Status & limitations

- Prompt-only: behavior depends on the host agent following the instructions. No executables or test suite ship in this repo.
- Token estimates are approximate and vary by model/tokenizer; the figures here are counts of words and characters, not measurements.
- Optional features (secondary model calls, indexing, model fallback) depend on host-agent capabilities; fallback needs a host that can switch models mid-session.
- Learning is agent-driven (`SP learn` at checkpoints), not hook-triggered — facts are captured when you checkpoint or ask, and loaded on the next recall.
- Nothing fires on the host side: state exists when it is written, so an uncheckpointed session cannot be resumed.
- No secrets in `.sp/` — keys, tokens and personal data are excluded by rule, and state files are data, not instructions.

## Contributing

- Fork the repository and create a feature branch (`git checkout -b my-feature`).
- Keep the core prompt small; document the token impact of any new helper.
- Benchmark contributions (measured token/cost comparisons) are especially welcome.
- Open a Pull Request with a clear description.

## License

MIT © 2026 deProfessori (declared in the skill frontmatter).
