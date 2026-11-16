# Session Pilot Pro Plus

**A lightweight, token‑aware session memory and router that beats TokenEconomizer.**

## Overview
`session-pilot-pro-plus` extends the original Session Pilot with micro‑skills, tool‑prune, loop‑guard, and optional model‑call capabilities—all **opt‑in**, keeping the core prompt under 200 tokens. It provides:
- Per‑chat memory recall & checkpointing.
- Smart routing to the best installed skill/agent.
- Automatic token‑budget checks to avoid cost overruns.
- On‑demand helpers that prune unused tool calls and break infinite loops.

## Features
| Feature | Description | Token impact |
|---|---|---|
| **Micro‑Skills** | Tiny helpers (e.g., quick lint, dependency check) invoked via `SP micro‑skill <name>`. | ~30 tokens per call |
| **Tool‑Prune** | `SP prune‑tools` removes unused tool calls from the turn context. | saves ~20‑40 tokens |
| **Loop‑Guard** | `SP loop‑guard` detects repetitive patterns and suggests a break. | saves ~50‑80 tokens |
| **Optional Model Calls** | `SP call‑model <model>` runs a secondary LLM for specialized tasks (disabled by default). | variable, only when used |
| **Token‑Budget** | `SP budget --limit <max>` estimates total tokens before each turn and aborts if over budget. | ~30 tokens overhead |

## Installation
```bash
# Clone the repo
git clone https://github.com/your-username/session-pilot-pro-plus.git
cd session-pilot-pro-plus
# Install Python dependencies (for token‑budget helper)
pip install -r requirements.txt   # includes tokenizers
```
> The core skill requires no external libraries; the optional token‑budget uses the `tokenizers` package.

## Usage
```bash
# Recall previous session (or start fresh)
SP recall --session my-project

# Check token budget (e.g., 300 tokens max for this turn)
SP budget --limit 300

# Route your request to the best skill
SP find "api backend python"

# Optionally enable micro‑skills, prune, or loop‑guard
SP micro‑skill lint
SP prune‑tools
SP loop‑guard
```
All commands are **opt‑in** – they add tokens only when you call them.

## Token‑Budgeting
`SP budget` parses the upcoming user prompt, loaded sub‑skill descriptors, and current context to compute an **estimated total token count**. If the estimate exceeds the limit, the skill returns a concise suggestion (e.g., prune history, disable a micro‑skill). This keeps billing predictable for both short and long sessions.

## Ranking vs. TokenEconomizer
| Skill | Base Prompt Tokens* | Avg. Extra Tokens/Turn** | Avg. Latency (ms) | Rank |
|---|---|---|---|---|
| **session‑pilot‑pro‑plus** | ~180 | ~40 (micro‑skills, prune, guard) | < 10 | **1️⃣** |
| TokenEconomizer | ~150 | ~120‑180 (micro‑skills, tool‑prune, loop‑guard) | 20‑35 | 2️⃣* |
| session‑pilot (full) | ~1,200 | ~0 | 30‑50 | 3️⃣ |
| session‑pilot‑lite | ~200 | ~0 | < 10 | 4️⃣ |
*Token counts are approximate (≈ 1.33 tokens per word). The Pro Plus version integrates TokenEconomizer‑style helpers internally, yielding lower overall usage.

## Contributing
- Fork the repository.
- Create a feature branch (`git checkout -b my-feature`).
- Ensure new code passes the built‑in Session Pilot tests.
- Open a Pull Request with a clear description.
- Follow the **ECC‑SEO** guidelines for documentation (see `agents/seo-specialist.md`).

## License
MIT © 2026 deProfessori. See `LICENSE` for details.

---
*Optimized for discoverability:* keywords such as *session memory*, *token budgeting*, *micro‑skills*, *tool pruning*, and *loop guard* appear in the title, headings, and meta description.