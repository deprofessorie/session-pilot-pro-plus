# Session Pilot Pro Plus

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/)
[![CI: Automated](https://img.shields.io/badge/CI-Automated%20(Ubuntu%20%2B%20Windows)-blue.svg)](.github/workflows/ci.yml)
[![Tests: 34/34 Passed](https://img.shields.io/badge/Tests-34%2F34%20Passed-brightgreen.svg)](scripts/verify.py)
[![Reliability Audit: 30/30](https://img.shields.io/badge/Stress%20Audit-30%2F30%20Passed-brightgreen.svg)](tests/stress_audit.py)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-0%20(Pure%20Stdlib)-orange.svg)](adapters/)
[![Release: v3.0.1](https://img.shields.io/badge/Release-v3.0.1%20(Honest%20Rebuild)-purple.svg)](https://github.com/deprofessorie/session-pilot-pro-plus)

**Lightweight, zero-dependency session memory, context discipline, and execution router for AI coding agents.**

</div>

---

Session Pilot Pro Plus provides **offline task-state persistence, repository facts harvesting, and senior-dev prompt discipline** in a single compact specification (< 180 tokens base). It is designed to work across both CLI harnesses (Claude Code, OpenCode, Codex CLI, Antigravity) and web-only interfaces (ChatGPT, Claude.ai) without requiring secondary model billing.

## 1. Architectural Model: Mechanism Grading

To maintain absolute transparency, capabilities in Session Pilot Pro Plus are classified by **mechanism**, not marketing claims:

- **● Natively Enforced:** Runs deterministic code in Python stdlib or lifecycle hooks regardless of model compliance.
- **◐ Prompt-Advisory:** Instructs the LLM on behavior/dialect; relies on model adherence.
- **○ Absent / Out of Scope:** Not provided by this package.

| Capability | Status | Mechanism | Details |
|---|:---:|---|---|
| **Task-State Checkpointing (done/next)** | **●** | Python stdlib (JSON / SQLite WAL) | Stores FIFO sliding window of 20 checkpoints with secret scrubbing |
| **Cross-Agent Shared Memory** | **●** | Isolated namespace files / SQLite | Synchronizes variables across subagents and independent sessions |
| **CWE-22 & Secret Sanitization** | **●** | Path hashing + regex redaction | Redacts JWTs, AWS keys, GitHub tokens; prevents directory escapes |
| **Repetition Loop Detection** | **●** | Checkpoint hash cycle detector | Hashes `done` actions; flags 3+ consecutive identical steps with 0 API calls |
| **Repo Facts Auto-Harvesting** | **●** | Post-turn command regex hook | Extracts `build_cmd`, `test_cmd`, `pkg_manager` from terminal executions |
| **Store Compaction** | **●** | Store checkpoint pruning | Trims checkpoint history array in the store (`sp.py compact`) |
| **Minimal-Diff Discipline (Ponytail)** | **◐** | Prompt instruction | Directs model to output minimal diffs, YAGNI, and transparency notes |
| **Caveman Dense Dialect** | **◐** | Prompt instruction | Strips conversational filler for token savings (inspired by Caveman) |
| **Model Tier Triage (T0..T3)** | **◐** | Advisory heuristic | Recommends appropriate model tier based on task complexity keywords |
| **Pre-Turn Token Budgeting** | **◐** | Character/word heuristic estimate | Pre-turn token estimate (heuristic +-15% or optional tiktoken) |
| **Tool Schema Payload Stripping** | **○** | Harness-dependent | Requires harness proxy/config hooks (e.g. TokenEconomizer deny-list) |

---

## 2. Competitor Context & Peer Baselines

Rather than claiming to replace peer tools with synthetic metrics, Session Pilot Pro Plus defines its clear architectural niche alongside them:

- **[TokenEconomizer](https://github.com/microsoft/TokenEconomizer)**: Excellent for automated log mining and harness-level schema deny-lists (measured 18.4–30.9% input reduction on 277 SWE-bench tasks). Requires Python 3.10+, harness hooks, and auxiliary LLM proposer calls.
- **[Ponytail](https://github.com/DietrichGebert/ponytail)**: Excellent for multi-harness rules configuration enforcing minimal diffs and YAGNI (measured -26% cost, -45% output tokens across 39 tasks).
- **[Caveman](https://github.com/JuliusBrussee/caveman)**: Measured 33.2% input token reduction and 21% cheaper per solved task on Terminal-Bench 4 by stripping filler words.
- **Session Pilot Pro Plus**: Fills the gap for **zero-dependency offline persistence, instant session recall across sessions, zero-billing fact harvesting, and portable single-file skill deployment across both CLI and web-based agents.**

---

## 3. Installation & Setup

### Option A: Pure Skill Mode (Zero Install)
Copy `SKILL.md` into your harness skills directory:
- Claude Code: `~/.claude/skills/session-pilot-pro-plus/SKILL.md`
- Gemini / Antigravity: `~/.gemini/config/skills/session-pilot-pro-plus/SKILL.md`
- OpenCode: `~/.config/opencode/skills/session-pilot-pro-plus/SKILL.md`

### Option B: Automatic Lifecycle Hooks (Claude Code Native)
To enable automatic `recall` on session start, safe non-destructive state flush on stop, and automatic test/build fact harvesting on Bash commands in Claude Code:
```bash
python hooks/install_hooks.py
```

---

## 4. CLI Quick Reference (`scripts/sp.py`)

```bash
# Session lifecycle
python scripts/sp.py recall [--session <id>]
python scripts/sp.py save --done "implemented auth" --next "write unit tests"
python scripts/sp.py mark-done [--session <id>]
python scripts/sp.py sessions list

# Memory & Facts
python scripts/sp.py fact set build_cmd "pnpm run build"
python scripts/sp.py fact list
python scripts/sp.py memory write --namespace team --key api_url "https://api.internal"
python scripts/sp.py memory read --namespace team --key api_url

# Execution Controls
python scripts/sp.py loop-guard [--threshold 3]
python scripts/sp.py compact [--keep 5]
python scripts/sp.py tier-check "fix race condition in transaction handler"
python scripts/sp.py budget "src/server.ts" --limit 2000
python scripts/sp.py find "react frontend router"
```

---

## 5. Verification & Test Suite

Session Pilot Pro Plus includes two automated test suites with 0 external dependencies:

```bash
# 1. Feature verification suite (31 tests across both adapters)
python scripts/verify.py --adapter json_file
python scripts/verify.py --adapter sqlite

# 2. Concurrency, corruption recovery, and security stress audit (30 scenarios)
python tests/stress_audit.py --adapter json_file
python tests/stress_audit.py --adapter sqlite

# 3. Storage latency & throughput empirical benchmark
python scripts/bench_storage.py --iterations 100

# 4. Multi-turn end-to-end A/B token & cost evaluation
python scripts/eval_ab.py

# 5. Interactive REPL for local testing
python scripts/repl.py --adapter json_file
```

---

## 6. License

MIT License © 2026 deProfessori
