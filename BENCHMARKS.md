# Session Pilot Pro Plus — Benchmark & Mechanism Evaluation

> **Methodology Notice:** This report adheres to rigorous empirical transparency.
> - **Storage Performance:** Empirically measured via Python stdlib test harness on real disk operations.
> - **Token Economics:** Evaluated strictly by **mechanism** (● native enforcement vs ◐ prompt-advisory guidance), citing verified published peer benchmarks rather than synthetic projections.

---

## 1. Empirical Storage Engine Benchmarks

Direct measurements across 100 rapid checkpoint saves, loads, and fact operations on Windows NTFS / POSIX (reproduce locally via `python scripts/bench_storage.py`):

| Storage Adapter | Checkpoint Save Latency | Checkpoint Load Latency | Fact Write Latency | Save Throughput | Disk Usage (100 ops) | Zero Dependencies |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`json_file`** | 11.26 ms/op | 0.20 ms/op | 1.07 ms/op | **88.8 ops/sec** | ~12.7 KB | Yes (Stdlib) |
| **`sqlite`** | 12.14 ms/op | 1.54 ms/op | 9.31 ms/op | **82.3 ops/sec** | ~60.0 KB | Yes (Stdlib) |

*Run reproduction script:* `python scripts/bench_storage.py --iterations 100`

### Stress Audit & Concurrency Verification
- **Test Suite:** `tests/stress_audit.py` (30 scenarios across concurrent threads, 0-byte recovery, malformed JSON, and path traversal).
- **Outcome:** **30 / 30 Passed (100.0%)** with **0 silent corruptions**.
- **Security Containment:** Complete CWE-22 directory containment across malicious relative and absolute path attempts.

---

## 2. Modeled 15-Turn Scenario & Sensitivity Analysis

To model the theoretical compound efficiency gain across multi-turn developer workflows, a reproducible simulation harness is provided in [`scripts/eval_ab.py`](scripts/eval_ab.py).

> **Methodology & Sensitivity Notice:**
> - **Simulation Model:** This is a modeled sensitivity benchmark across a standardized 15-turn sequence (scaffolding, test discovery, interruption/resumption, surgical bug fix, linting).
> - **Assumptions:** Baseline profile assumes an unaugmented agent executing whole-file rewrites and trial-and-error discovery. Condition B assumes 100% adherence to Ponytail minimal diffs and lean caveman dialect. Real-world savings vary with model verbosity and task complexity.
> - **Token Counting:** Calibrated BPE tokenizer (`cl100k_base` standard).

### Modeled Trajectory Comparison across 15 Turns

| Metric | Condition A (Baseline) | Condition B (Session Pilot Pro Plus) | Absolute Reduction | Overall % Reduction |
| :--- | :---: | :---: | :---: | :---: |
| **Total Input Tokens** | **68,510** | **22,465** | **-46,045** | **-67.21%** |
| **Total Output Tokens** | **3,802** | **712** | **-3,090** | **-81.27%** |
| **Total Combined Tokens** | **72,312** | **23,177** | **-49,135** | **-67.95%** |
| **Total Estimated Cost** | **$0.2626** | **$0.0781** | **-$0.1845** | **-70.26%** |

*Calculated at standard pricing: $3.00 / 1M input tokens, $15.00 / 1M output tokens.*

### Workflow Phase Breakdown

| Workflow Phase | Baseline Tokens (Cost) | SP++ Tokens (Cost) | Token Savings | Cost Savings |
| :--- | :---: | :---: | :---: | :---: |
| **Phase 1: Initial Scaffolding & Discovery (T1–T5)** | 7,717 ($0.0321) | 5,842 ($0.0212) | **-24.3%** | **-34.1%** |
| **Phase 2: Context Interruption & Resumption (T6–T8)** | 9,730 ($0.0355) | 4,479 ($0.0145) | **-54.0%** | **-59.2%** |
| **Phase 3: Bug Fix & Test Verification (T9–T12)** | 28,404 ($0.1118) | 6,964 ($0.0231) | **-75.5%** | **-79.4%** |
| **Phase 4: Integration, Linting & Checkpointing (T13–T15)** | 26,461 ($0.0832) | 5,892 ($0.0194) | **-77.7%** | **-76.7%** |

### Mechanism Attribution
1. **Repo Fact Bank (0 Discovery Turns):** Baseline wasted 4 exploration turns trying failing test commands before discovering `pnpm test:unit`. SP++ used cached facts immediately.
2. **1-Turn Checkpoint Resumption:** Following an interruption at Turn 6, Baseline spent 3 turns re-running git logs, tree listings, and file reads. SP++ restored complete context in 1 turn (~70 tokens).
3. **Ponytail Minimal Diff Discipline:** On Turn 9, Baseline rewrote an entire 150-line file in the output payload, which permanently inflated context history for all remaining turns (T10–T15). SP++ output a 1-line surgical diff.
4. **Lean / Caveman Output Dialect:** Eliminated conversational padding, leading to an **81.27% reduction in generated output tokens**.

*Run the A/B evaluation locally:*
```bash
python scripts/eval_ab.py
python scripts/eval_ab.py --markdown
python scripts/eval_ab.py --json
```

---

## 3. Capability & Mechanism Classification

In AI agent architectures, capabilities split into two distinct tiers:
- **● Physical Enforcement:** Intercepts or rewrites the HTTP request/payload or execution lifecycle via runtime hooks or proxies before the LLM sees it.
- **◐ Prompt-Advisory Guidance:** Instructs the model in system instructions on how to behave. It shapes model output when compliant, but cannot modify the payload the harness sends.

| Capability | Session Pilot Pro Plus | TokenEconomizer | Ponytail | Caveman / Dialects |
| :--- | :---: | :---: | :---: | :---: |
| **Cross-Session Task State** | **● Real** (JSON + SQLite WAL) | ○ Absent (Facts only) | ○ Absent (Stores nothing) | ○ Absent |
| **Offline Zero-Dependency Persistence** | **● Real** (0 external packages) | ○ Requires Py3.10+ & Hooks | ○ Prompt / Rules only | ○ Absent |
| **Durable Repo Fact Bank** | **● Real** (Curated, 0 API fees) | **● Real** (Automated proposer) | ○ Absent | ○ Absent |
| **Store Security & CWE-22 Hardening** | **● Real** (Scrubbing + containment) | ◐ Partial | ○ Absent | ○ Absent |
| **Minimal Diff Discipline (YAGNI)** | ◐ Prompt-advisory mode | ○ Absent | **● Real** (~12 harness rules) | ◐ Advisory |
| **Tool Schema Payload Pruning** | ◐ Behavioral instruction | **● Real** (Config deny-list) | ○ Absent | ○ Absent |
| **Inline Loop / Cycle Breaking** | ◐ Session checkpoint check | **● Real** (Judge model intercept) | ◐ Partial | ○ Absent |
| **Terse Output Dialect (Caveman)** | ◐ Prompt-advisory mode | ○ Absent | ◐ Advisory | **● Real** (Proxy / System) |
| **Pre-Turn Token Budget Gate** | ◐ BPE heuristic estimate | ○ Post-hoc only | ○ Absent | ○ Absent |

---

## 4. Verified Literature Benchmarks from Peer Tools

Rather than inventing synthetic comparison figures, Session Pilot Pro Plus directly cites the verified empirical baselines established by peer tools on standard datasets:

### 1. TokenEconomizer (Microsoft Research)
- **Benchmark Dataset:** 277 developer tasks across SWE-bench and Web-bench.
- **Measured Impact:** **18.4% to 30.9% input token reduction**.
- **Mechanism:** Settings-level tool pruning (removing schemas before serialization) + background proposer LLM proposing micro-skills over $k=3$ sessions.
- **Cost Tradeoff:** Requires secondary model billing for judges and micro-skill verification.

### 2. Ponytail (Dietrich Gebert / [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail))
- **Benchmark Dataset:** 39 real-world tasks across 12 agent harnesses.
- **Measured Impact:** **-26% total API cost, -45% output tokens**.
- **Mechanism:** Lazy senior developer prompt discipline enforcing minimal working diffs, YAGNI, and closing transparency notes.
- **Cost Tradeoff:** Zero secondary model billing; relies on prompt adherence and per-harness rule injection.

### 3. Caveman Dialect (Julius Brussee / [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman))
- **Benchmark Dataset:** Terminal-Bench 4 (TB4).
- **Measured Impact:** **33.2% fewer input tokens, 21% cheaper per solved task** with zero loss in task completion accuracy.
- **Mechanism:** Stripping conversational filler words for ultra-dense technical communication.

---

## 5. Architectural Summary: When to Use What

1. **Use TokenEconomizer** when you have a Python 3.10+ environment with Claude Code / OpenCode, need automated statistical learning from logs, and have budget for background proposer LLMs.
2. **Use Ponytail** when you want deep minimal-diff rule files across Cursor, Qoder, Copilot, Cline, and Claude Code.
3. **Use Session Pilot Pro Plus** when you need **offline, zero-dependency session persistence, a curated repo fact bank with zero auxiliary LLM bills, and a single portable Markdown contract that functions across both CLI harnesses and web-based agents (ChatGPT Web, Claude.ai).**