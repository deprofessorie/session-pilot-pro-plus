# Unified Memory & Multi-Agent Handoff

> Inspired by Unified-Memory. Durable state synchronization across sessions and subagents.

## Commands

- `SP memory sync [namespace]` — Synchronizes durable key/values across concurrent or sequential agents.
- `SP memory handoff <agent-role>` — Formats and emits a structured handoff payload for delegating work to another agent or subagent.

## Handoff Payload Schema
```markdown
### Agent Handoff Payload
- **Source Session:** `<session-id>`
- **Target Role:** `<agent-role>`
- **Active Goal:** `<goal>`
- **Completed Diffs:** `<files modified>`
- **Verified Facts:** `<test/build commands>`
- **Next Immediate Action:** `<step>`
- **Known Risks / Unverified:** `<risks>`
```
