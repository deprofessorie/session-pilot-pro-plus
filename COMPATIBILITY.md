# Agent Compatibility Matrix

Session Pilot Pro Plus operates in two tiers:
1. **Prompt-Only Mode:** Works universally across all AI agents (including web agents like ChatGPT, Claude.ai) as behavioral guidelines (<180 tokens).
2. **Hook & Storage Mode:** Full deterministic persistence (JSON/SQLite WAL) and automatic lifecycle hooks on supported local developer workstations.

---

## Capability Support by Harness

| Capability | Mechanism | Claude Code | Gemini CLI / Antigravity | OpenCode | Cursor / Codex CLI | Web (ChatGPT / Claude.ai) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Session State (save/recall)** | ● Native Store | ✅ (Hook/CLI) | ✅ (Rule/CLI) | ✅ (CLI) | ✅ (CLI) | ◐ (In-context) |
| **Session Start/Stop Hooks** | ● Native / ◐ Advisory | ✅ (`settings.json`) | ◐ Advisory (`user_rules`) | ◐ Advisory¹ | ◐ Advisory | ❌ N/A |
| **Repo Fact Bank (fact set/get)** | ● Native Store | ✅ | ✅ | ✅ | ✅ | ◐ (In-context) |
| **Auto-Harvest Facts Hook** | ● PostToolUse Hook | ✅ (`Bash` matcher) | ◐ (`sp.py harvest`) | ◐ (`sp.py harvest`) | ◐ (`sp.py harvest`) | ❌ N/A |
| **Cross-Agent Memory (sync/read/write)** | ● Native Store | ✅ | ✅ | ✅ | ✅ | ❌ N/A |
| **Repetition Loop Guard** | ● Checkpoint Hash | ✅ | ✅ | ✅ | ✅ | ◐ Advisory |
| **Store Compaction** | ● Native Store | ✅ | ✅ | ✅ | ✅ | ◐ Advisory |
| **Ponytail Minimal Diffs (YAGNI)** | ◐ Prompt Advisory | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Caveman Dialect** | ◐ Prompt Advisory | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Model Tier Triage (T0..T3)** | ◐ Advisory Heuristic | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Pre-Turn Token Budget** | ◐ Advisory Heuristic | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Skill Discovery (SP find)** | ● Filesystem Scan² | ✅ | ✅ | ✅ | ✅ | ❌ N/A |

> ¹ OpenCode loads JavaScript plugins (`plugin/*.js`); Python hook auto-invocation in OpenCode requires calling `python scripts/sp.py` from CLI or wrapping in a JS plugin.  
> ² On web agents or sandboxes without local filesystem access, `SP find` degrades to in-context inspection.

---

## Setup Instructions

### 1. Claude Code
Install hooks to enable automatic turn/session persistence and fact harvesting:
```bash
python hooks/install_hooks.py
```
This registers `SessionStart`, `Stop`, and `PostToolUse` (Bash matcher) in `~/.claude/settings.json`.

### 2. Antigravity / Gemini CLI
Add Session Pilot recall and save to your persistent rules (`~/.gemini/config/skills/` or `user_rules`).

### 3. OpenCode / Cursor / Codex CLI
Copy `SKILL.md` to your skills folder and invoke commands directly via chat conventions (`SP recall`, `SP save`, `SP fact set`).
