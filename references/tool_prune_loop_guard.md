# Tool Pruning & Loop Guard

> Mechanism Classification:
> - **Loop Guard:** ● Enforced natively via checkpoint hash comparison (`sp.py loop-guard`).
> - **Tool Pruning:** ◐ Advisory / architectural note. True schema suppression requires harness-level proxy/hook integration.

---

## 1. Loop Guard & Cycle Breaker (`SP loop-guard`)

### Mechanism (● Native)
`sp.py loop-guard` inspects recent session checkpoints in the storage adapter. It computes SHA-256 hashes of the `done` actions and detects when an agent repeats identical or near-identical steps $\ge 3$ times consecutively.

Unlike TokenEconomizer (which executes a secondary LLM judge model call billed to the user), Session Pilot Pro Plus performs this check **offline on stored checkpoint data with zero token cost and zero latency**.

### CLI Usage
```bash
python scripts/sp.py loop-guard [--session <id>] [--threshold 3] [--verbose]
```

### Prompt Convention
When an agent notices repeated failures or tests failing with identical output, it triggers `SP loop-guard` to verify if a cycle has formed and pivot to an alternative hypothesis.

---

## 2. Tool Schema Pruning (`SP prune-tools`)

### Reality & Mechanism Boundary
- **What a prompt can do (◐ Advisory):** Advise the model to ignore unused tool schemas and restrict tool calls to relevant candidates.
- **What a prompt cannot do:** A prompt or skill file cannot strip tool schema definitions out of the HTTP payload sent to the LLM API, because harnesses serialize tools into the request JSON before model generation begins.
- **True payload pruning:** Requires harness-level settings hooks (such as TokenEconomizer's config deny-lists or custom client proxies).
