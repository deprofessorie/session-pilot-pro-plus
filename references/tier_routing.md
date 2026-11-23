# Model Tier Arbitrage & Task Routing

> Inspired by Efficiency-Router. Prevents burning scarce premium quota on routine tasks.

## Triage Levels

| Tier | Task Type | Example | Recommended Model & Action |
|---|---|---|---|
| **T0 Trivial** | Chit-chat, known facts, 1-line edits | "What is HTTP 429?", "fix typo" | Direct answer; `flash_lite` / `flash`; 0 tools |
| **T1 Mechanical** | Bulk reads, grep, search, format conversions | "Search 30 files for deprecated API" | Cheap model (`flash`) |
| **T2 Standard** | Well-specified features, bug fixes with repro | "Implement JWT expiry validation" | Balanced model (`pro` or self) |
| **T3 Hard** | Complex architecture, race conditions, subtle security | "Design consensus failover protocol" | Flagship reasoning model (`inherit` / top tier) |

## Commands
- `SP tier-check "<task>"` — Evaluates task hardness and outputs target tier recommendation.
- `SP route-model` — Generates subagent delegation directives based on active tier.
