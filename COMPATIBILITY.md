# Agent Compatibility Matrix

Session Pilot Pro Plus is a **prompt-only skill** — it works wherever the agent reads and follows Markdown instructions. However, not all agents support every capability equally. This matrix documents what works where.

---

## Capability Support by Agent

| Capability | OpenCode | Claude Code | Codex CLI | Cursor | Gemini CLI | Antigravity | Qoder | ChatGPT / Claude.ai (web) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Core: SP recall / save** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Core: SP find / list** | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ⚠️² |
| **Core: SP budget** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Core: SP clean** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Core: SP mark-done** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Core: SP optimizers** | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ⚠️² |
| **Core: SP import** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Opt-in: SP prune-tools** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Opt-in: SP loop-guard** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Opt-in: SP micro-skill** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Opt-in: SP call-model** | ⚠️³ | ⚠️³ | ⚠️³ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Opt-in: SP index / query** | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ |
| **Opt-in: SP persist** | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ |
| **Opt-in: SP memory sync** | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ |
| **Opt-in: SP learn** | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ |
| **Opt-in: SP fallback** | ⚠️³ | ⚠️³ | ⚠️³ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Lean mode** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Style mirroring** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Guardrails** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Session lifecycle** | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ | ⚠️⁴ |
| **Discovery (SP list)** | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ✅¹ | ⚠️² |

---

## Legend

- ✅ **Full support** — works out of the box via prompt instructions
- ⚠️ **Partial / requires setup** — needs storage adapter, multi-model config, or file access
- ❌ **Not supported** — agent lacks required capability
- ¹ Requires **file system access** to scan skill directories (`~/.config/opencode/skills`, `~/.claude/skills`, etc.)
- ² Web agents cannot scan local filesystem — `SP list`/`SP find` work only from skills already in context
- ³ Requires agent to support **mid-session model switching** (OpenCode: yes via model parameter; others: varies)
- ⁴ Requires **storage adapter** implementation — see `STORAGE_ADAPTERS.md`. Works in-memory during conversation but not across context resets without adapter.

---

## What "Prompt-Only" Means in Practice

| Agent Type | Memory Persistence | Skill Discovery | Cross-Session Learning |
|---|---|---|---|
| **Local agents with file access** (OpenCode, Claude Code, Codex, Cursor, Gemini CLI) | Via JSON/SQLite adapter | Full scan of skill dirs | Via adapter |
| **Local agents w/o file access** (some CLI tools) | In-conversation only | Manual `SP import` | In-conversation only |
| **Web agents** (ChatGPT, Claude.ai, Gemini web) | In-conversation only | Skills in custom instructions only | In-conversation only |

---

## Recommended Setup by Agent

### OpenCode (this repo's primary target)
```markdown
# AGENTS.md (already configured)
# Skill loads automatically, has file access
# Use JSON file adapter for persistence:
#   SP storage set json_file ~/.session-pilot-pro-plus
```

### Claude Code
```markdown
# ~/.claude/CLAUDE.md
# Paste SKILL.md contents or:
# @import "~/.claude/skills/session-pilot-pro-plus/SKILL.md"

# For persistence, agent can use Bash tool to run Python adapter
```

### Codex CLI
```markdown
# ~/.codex/AGENTS.md
# Same as OpenCode — file access available
```

### Cursor
```markdown
# .cursor/rules/session-pilot-pro-plus.mdc
---
alwaysApply: true
---
# Paste SKILL.md contents
```

### Web Agents (ChatGPT, Claude.ai)
```markdown
# Custom Instructions → paste SKILL.md
# No persistence, no discovery — but lean mode, style mirroring, guardrails all work
```

---

## Verification Checklist for New Agents

When adding support for a new agent, verify:

- [ ] Core commands execute without error
- [ ] Lean mode reduces verbosity
- [ ] Token budget blocks over-limit turns
- [ ] Style mirroring detects and persists pattern
- [ ] Guardrails redact secrets, refuse scope creep
- [ ] `SP list` shows installed skills (if file access)
- [ ] Storage adapter works for persistence (if file access)

---

## Contributing

Add a row for your agent. Test the full `EVALUATION.md` suite and report results.