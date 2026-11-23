# Unified Memory & Multi-Agent Handoff

> Mechanism Classification:
> - **Cross-Agent Memory:** ● Enforced natively via storage adapters (`sp.py memory write/read/sync`).
> - **Agent Handoff:** ◐ Standardized structured text payload for delegation across subagents.

---

## 1. Cross-Agent Shared Memory (`SP memory`)

### Mechanism (● Native Store)
The storage adapters implement isolated, sanitized memory namespaces (`HOME/memory/<namespace>/<key>.json` or SQLite `memory` table with CWE-22 sanitization). Any agent or script with access to the store can read/write shared variables.

### CLI Commands
```bash
# Write shared key
python scripts/sp.py memory write --namespace team-alpha --key framework fastapi

# Read shared key
python scripts/sp.py memory read --namespace team-alpha --key framework

# List namespace keys
python scripts/sp.py memory list --namespace team-alpha

# Sync / summarize all active namespaces
python scripts/sp.py memory sync
```

---

## 2. Multi-Agent Handoff Schema (`SP memory handoff`)

When delegating a task to a subagent (via `invoke_subagent` or board messages), format the instruction using this structured schema to minimize context overhead:

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
