# Agent Compatibility Matrix

Session Pilot Pro Plus operates in two tiers:
1. **Prompt-Only Mode:** Works universally across all AI agents (including web agents like ChatGPT, Claude.ai) as behavioral guidelines (<180 tokens).
2. **Hook & Storage Mode:** Full deterministic persistence (JSON/SQLite WAL) and automatic lifecycle hooks on local developer workstations (Claude Code, OpenCode, Antigravity, Cursor).

---

## Capability Support by Harness

| Capability | Mechanism | OpenCode | Claude Code | Codex CLI | Cursor | Gemini CLI / Antigravity | Web (ChatGPT / Claude.ai) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Session State (save/recall)** | ● Native Store | ✅ (Hook/CLI) | ✅ (Hook/CLI) | ✅ (CLI) | ✅ (CLI) | ✅ (Rule/CLI) | ◐ (In-context) |
| **Session Start/Stop Hooks** | ● Native Hook | ✅ (`hooks.json`) | ✅ (`settings.json`) | ◐ Advisory | ◐ Advisory | ✅ (`user_rules`) | ❌ N/A |
| **Repo Fact Bank (fact set/get)** | ● Native Store | ✅ | ✅ | ✅ | ✅ | ✅ | ◐ (In-context) |
| **Auto-Harvest Facts Hook** | ● Post-turn Hook | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ N/A |
| **Cross-Agent Memory (sync/read/write)** | ● Native Store | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ N/A |
| **Repetition Loop Guard** | ● Checkpoint Hash | ✅ | ✅ | ✅ | ✅ | ✅ | ◐ Advisory |
| **Store Compaction** | ● Native Store | ✅ | ✅ | ✅ | ✅ | ✅ | ◐ Advisory |
| **Ponytail Minimal Diffs (YAGNI)** | ◐ Prompt Advisory | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Caveman Dialect** | ◐ Prompt Advisory | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Model Tier Triage (T0..T3)** | ◐ Advisory Heuristic | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Pre-Turn Token Budget** | ◐ Advisory Heuristic | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Skill Discovery (SP find)** | ● Filesystem Scan | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ N/A |

---

## Setup Instructions

### 1. Claude Code
Install hooks to enable automatic turn/session persistence:
```bash
python hooks/install_hooks.py
```
This updates `~/.claude/settings.json` with `SessionStart` and `SessionStop` hooks calling `sp.py`.

### 2. OpenCode
Configures `~/.config/opencode/hooks.json` to execute `session_start.py` and `session_stop.py`.

### 3. Antigravity / Gemini CLI
Add Session Pilot recall and save to your persistent rules (`~/.gemini/config/skills/` or `user_rules`).
