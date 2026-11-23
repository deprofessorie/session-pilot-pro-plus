---
name: session-pilot-pro-plus
description: Ultra-lightweight (<180 tokens) agent memory and cost control router.
license: MIT
metadata:
  version: "3.0.0"
---

# Session Pilot Pro Plus (Micro-Core)

Compact agent memory & cost control router. Load details from `references/`.

## Conventions
1. **Memory:** `SP recall [--session ID]` loads state; `SP save --done X --next Y [--ponytail M]` checkpoints; `SP mark-done` finishes.
2. **Budget:** `SP budget "<text or file>" [--limit N]` estimates prompt tokens before spend.
3. **Routing:** `SP find "<keywords>"` routes skills; `SP tier-check "<task>"` triages T0..T3.
4. **On-Demand Modes (`references/`):**
   - `SP ponytail [lite|full|ultra|off]` — Minimal diff & transparency note (`references/ponytail.md`).
   - `SP fact [set|get|list|delete]` — Repo micro-skills bank (`references/facts_microskills.md`).
   - `SP loop-guard` — Checkpoint repetition cycle breaker (`references/tool_prune_loop_guard.md`).
   - `SP compact` & `SP caveman [on|off]` — Compaction & dense dialect (`references/compression_dialects.md`).
   - `SP memory [write|read|sync|list]` — Cross-agent memory & handoff (`references/memory_sync.md`).

## Lean Mode (Always Active)
Answer directly. Quote targeted lines. Zero filler. Redact secrets.
