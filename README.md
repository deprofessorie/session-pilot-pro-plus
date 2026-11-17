# Session Pilot Pro Plus

**A lightweight, token-aware session memory and skill-router agent skill.**

## Overview

`session-pilot-pro-plus` is a **prompt-only skill**: a single Markdown file that instructs an AI coding agent to recall session state, route requests to the best available skill, checkpoint progress, and watch token usage. There is no runtime code, CLI binary, or external dependency in this repository.

It provides:
- Per-chat memory recall & checkpointing.
- Routing guidance to the best installed skill/agent.
- Token-budget checks to help avoid cost overruns.
- Opt-in helpers for pruning unused tool calls and breaking repetitive loops.

## What's in this repo

| File | Purpose |
|---|---|
| `README.md` | This overview |
| `session-pilot-pro_SKILL.md` | The skill itself (frontmatter + agent instructions) |

## How it works

Once the skill is loaded into your agent (Qoder, or any harness that supports Markdown skills), the `SP ...` commands are **chat conventions**: you type them in the conversation and the agent performs the described behavior. They are not shell commands.

Core behaviors (always described in the skill):
- `SP recall [--session ID]` — restore prior chat state or start fresh.
- `SP find "<keywords>"` — route the request to the best matching skill.
- `SP save --done "<action>" --next "<step>"` — checkpoint progress for later resumption.
- `SP import <PATH>` — wire project-level rules into the session.
- `SP budget --limit <max>` — the agent estimates the upcoming turn's token usage and suggests pruning if over the limit.

Opt-in helpers (add tokens only when invoked):
- `SP micro-skill <name>` — run a tiny focused helper (e.g., quick lint, dependency check).
- `SP prune-tools` — drop unused tool calls from the turn context.
- `SP loop-guard` — detect repetitive patterns and suggest a break.
- `SP call-model <model>` — request a secondary model call (disabled by default; requires host support).
- `SP index <PATH>` / `SP query "<text>"` — lightweight semantic search over files.
- `SP persist set|get <key>` — small per-project key/value store.
- `SP memory sync` — sync durable cross-agent context.

## Installation

No dependencies and nothing to build. Install the skill file into your agent's skills directory (rename it to `SKILL.md` inside a `session-pilot-pro-plus` folder if your harness expects that layout), or paste its contents into your agent's persistent instructions.

## Token costs

All token figures in the skill file are **rough design estimates** (≈ 1.33 tokens per word), not measured benchmarks. The core prompt is designed to stay under ~200 tokens; optional helpers add tokens only when you invoke them.

## Status & limitations

- Prompt-only: behavior depends on the host agent following the instructions. This repo contains no executables, Python helpers, or test suite.
- Token estimates are approximate and vary by model and tokenizer.
- Optional features such as secondary model calls and vector indexing depend on what the host agent supports.

## Contributing

- Fork the repository.
- Create a feature branch (`git checkout -b my-feature`).
- Keep the core prompt small; document the token impact of any new helper.
- Open a Pull Request with a clear description.

## License

MIT © 2026 deProfessori (declared in the skill frontmatter).