# Repository Micro-Skills & Fact Bank

> Inspired by UC Berkeley & Microsoft Research TokenEconomizer. Eliminates 18–31% of exploration token burn.

## Purpose
Agents waste thousands of tokens discovering basic repository facts across sessions (how to run tests, where build artifacts live, custom path aliases, local database ports). Micro-skills store these once and auto-inject them at session start.

## Commands

- `SP fact set <key> <value>` — Store a repository fact.
  - Examples:
    - `SP fact set test_cmd "pytest -m unit -q"`
    - `SP fact set build_cmd "pnpm build"`
    - `SP fact set alias "@app/* -> src/*"`
    - `SP fact set env "REDIS_URL=redis://localhost:6379/0"`
- `SP fact get <key>` — Retrieve a specific fact.
- `SP fact list` — List all verified repository facts for the current project.
- `SP fact export` — Format facts for direct prompt injection into subagents.
- `SP fact delete <key>` — Remove an obsolete fact.

## Auto-Injection Protocol
On `SP recall`, the agent checks the project's fact bank. If facts exist, they are loaded immediately into the active session context, eliminating repetitive discovery commands (`ls`, `find`, `cat package.json`, trial-and-error test runs).
