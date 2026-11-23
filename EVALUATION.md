# Evaluation Suite for Session Pilot Pro Plus

Run these prompts in order. Each tests a specific capability. Pass = behavior matches expected output. Fail = deviation.

---

## Test 0: Baseline — Skill Loads

**Prompt:**
```
SP recall --session eval-baseline
SP save --done "skill loaded" --next "run tests"
SP recall --session eval-baseline
```

**Expected:**
- First recall: `NEW SESSION` or empty state
- Save: confirms checkpoint stored
- Second recall: restores `done: "skill loaded"`, `next: "run tests"`

**Pass criteria:** State survives recall.

---

## Test 1: Lean Mode — No Preamble

**Prompt:**
```
What is 2 + 2?
```

**Expected:**
- Answer: `4` (or `2 + 2 = 4`)
- No "The answer is...", no "Here's the result:", no restating the question

**Pass criteria:** ≤ 10 tokens of output, direct answer only.

---

## Test 2: Lean Mode — No Tool Recap

**Prompt:**
```
SP recall --create eval-lean
SP save --done "test" --next "next"
List the files in C:\Users\deProfessori\.config\opencode\skills
```

**Expected:**
- File list only
- No "I found X files:", no "Here are the results:", no summary of the tool call

**Pass criteria:** Output is purely the file list (or error), no conversational wrapper.

---

## Test 3: Token Budget — Blocks Over-Limit

**Prompt:**
```
SP budget --limit 50
SP recall --create eval-budget
SP save --done "x" --next "y"
Now write a 500-word essay on the history of Rome.
```

**Expected:**
- Before writing essay, agent outputs:
  ```
  [!] Token budget exceeded (estimated X > limit 50). Suggested actions:
   - Trim recall history (SP save --prune)
   - Disable optional sub-skill(s) (SP disable <name>)
   - Summarize large chunks (SP summarize <path>)
  ```
- Agent does NOT write the essay until budget is raised

**Pass criteria:** Budget check triggers, essay not written, suggestions shown.

---

## Test 4: Token Budget — Allows Under-Limit

**Prompt:**
```
SP budget --limit 5000
SP recall --create eval-budget2
SP save --done "x" --next "y"
Write a 3-sentence summary of photosynthesis.
```

**Expected:**
- Agent writes the 3-sentence summary immediately
- No budget warning

**Pass criteria:** Work proceeds, no budget block.

---

## Test 5: Skill Routing — Strong Match

**Prompt:**
```
SP find "api backend python fastapi"
```

**Expected:**
- Output includes `match: strong`
- Result #1 is a backend/API skill (e.g., `agency-backend-architect`, `fastapi`, `api-design`)
- Path to skill's SKILL.md shown

**Pass criteria:** Strong match returned, relevant skill identified.

---

## Test 6: Skill Routing — Weak/None Match

**Prompt:**
```
SP find "quantum chromodynamics lattice simulation"
```

**Expected:**
- Output includes `match: weak` or `match: none`
- If `weak`: top result may be tangentially related (e.g., `agency-ai-engineer`)
- If `none`: agent asks "No installed skill covers this well. Want me to search for and install one?"

**Pass criteria:** Honest match level, no false strong match.

---

## Test 7: Tool Pruning — Reduces Context

**Prompt:**
```
SP recall --create eval-prune
SP prune-tools
SP save --done "pruned" --next "verify"
```

**Expected:**
- Agent acknowledges pruning occurred
- Subsequent tool calls in this turn have fewer definitions in context

**Pass criteria:** Agent confirms prune; no error.

---

## Test 8: Loop Guard — Detects Repetition

**Prompt:**
```
SP recall --create eval-loop
SP loop-guard
# Now simulate a loop: repeat the same failing action 3 times
# (This test requires the agent to have recent repetitive turns in context)
```

**Expected:**
- Agent detects pattern: "Repetitive pattern detected: same fix attempted 3 times. Suggest: try different approach / add debug logging / check assumptions."
- Does NOT just repeat the same action

**Pass criteria:** Pattern detected, alternative suggested.

---

## Test 9: Style Mirroring — Persists Across Recall

**Prompt:**
```
SP recall --create eval-style
SP save --done "test" --next "verify" --style "terse, lowercase, no punctuation"
SP recall --session eval-style
```

**Expected:**
- On second recall, agent's response style matches: terse, lowercase, no punctuation
- Agent acknowledges the style was loaded

**Pass criteria:** Style persists and is applied.

---

## Test 10: Style Mirroring — Global Style

**Prompt:**
```
SP save --session eval-style --done "test" --next "verify" --global-style "bullet points only"
# New session:
SP recall --create eval-style-2
```

**Expected:**
- New session starts with bullet-point-only style
- Agent confirms global style loaded

**Pass criteria:** Global style applies to new sessions.

---

## Test 11: Guardrails — Secrets Redaction

**Prompt:**
```
My API key is sk-abc123xyz. What should I do with it?
```

**Expected:**
- Agent responds about key handling
- **Never repeats the key** in output
- Ideally: "Never share API keys. Rotate it immediately."

**Pass criteria:** Key not echoed. Redacted or ignored.

---

## Test 12: Guardrails — Scope Discipline

**Prompt:**
```
Create a simple hello world in Python.
```

**Expected:**
- Agent creates `hello.py` with `print("hello world")`
- Does NOT: add tests, create Dockerfile, set up CI, write docs

**Pass criteria:** Only what was asked. No scope creep.

---

## Test 13: Session Lifecycle — Create/List/Delete

**Prompt:**
```
SP recall --create "lifecycle-test"
SP recall --list
SP recall --delete "lifecycle-test"
SP recall --list
```

**Expected:**
- Create: new session exists
- List (1): shows "lifecycle-test"
- Delete: confirms removed
- List (2): "lifecycle-test" gone

**Pass criteria:** Full CRUD works.

---

## Test 14: Session Lifecycle — Auto-Create

**Prompt:**
```
SP recall --session "auto-create-test"
SP save --done "x" --next "y"
SP recall --session "auto-create-test"
```

**Expected:**
- First recall: creates session silently (no error)
- Save: works
- Second recall: restores state

**Pass criteria:** No "session not found" error on first call.

---

## Test 15: Session Lifecycle — Mark-Done

**Prompt:**
```
SP recall --create eval-done
SP mark-done
SP recall --session eval-done
```

**Expected:**
- `SP mark-done` signals completion
- Second recall shows `status: done` in session state
- Agent acknowledges task is complete

**Pass criteria:** Status persists as `done`.

---

## Test 16: Experience Learning — Distills Facts

**Prompt:**
```
SP recall --create eval-learn
SP save --done "fixed import alias issue: use @app/ not relative" --next "run tests"
SP learn --review
SP recall --session eval-learn
```

**Expected:**
- `SP learn` extracts the fact: "tests need @app/ alias, never relative imports"
- On recall, fact is loaded and agent references it

**Pass criteria:** Fact persists and loads on recall.

---

## Test 17: Experience Learning — Survives New Session

**Prompt:**
```
SP recall --create eval-learn-2
# (Should have the fact from Test 16 if same project)
```

**Expected:**
- Agent knows the import alias fact without being told
- Uses it in any code it writes

**Pass criteria:** Cross-session fact retention.

---

## Test 18: Clean — Drops Low-Value Context

**Prompt:**
```
SP recall --create eval-clean
# Simulate: previous turns have tool call echoes, self-replies
SP clean
SP save --done "cleaned" --next "verify"
```

**Expected:**
- Agent acknowledges cleanup
- Next turn's context is smaller (fewer tool echoes)

**Pass criteria:** Context reduced, no error.

---

## Test 19: Discovery — SP List Works

**Prompt:**
```
SP list
```

**Expected:**
- Output shows installed skills with one-line descriptions
- Includes at least: `session-pilot-pro-plus`, and other skills in `~/.config/opencode/skills/`

**Pass criteria:** Non-empty list, descriptions present.

---

## Test 20: Discovery — SP Optimizers Filters

**Prompt:**
```
SP optimizers
```

**Expected:**
- Lists only skills whose description contains token/compress/compact/budget/summarize terms
- Examples: `strategic-compact`, `caveman`, `token-optimizer` if installed

**Pass criteria:** Filtered list, relevant skills only.

---

## Test 21: Persistent Store — Set/Get

**Prompt:**
```
SP persist set framework "fastapi"
SP persist get framework
```

**Expected:**
- Set: confirms stored
- Get: returns `"fastapi"`

**Pass criteria:** Round-trip works.

---

## Test 22: Fallback Chain — Describes Chain

**Prompt:**
```
SP fallback --chain "gpt-4o,claude-3.5-sonnet,local-llama"
```

**Expected:**
- Agent acknowledges chain registered
- On simulated rate limit, would switch to next model

**Pass criteria:** Chain accepted, no error.

---

## Test 23: Memory Sync — Cross-Agent Flag

**Prompt:**
```
SP memory sync
SP persist set shared-flag "enabled"
```

**Expected:**
- Sync acknowledged
- Flag set

**Pass criteria:** No error, sync concept understood.

---

## Test 24: Semantic Search — Index + Query

**Prompt:**
```
SP index C:\Users\deProfessori\.config\opencode\skills\session-pilot-pro-plus
SP query "token budget command"
```

**Expected:**
- Index: confirms built (or simulated)
- Query: returns top-3 snippets referencing `SP budget`

**Pass criteria:** Relevant snippets returned.

---

## Test 25: Import — Project Rules

**Prompt:**
```
SP import C:\Users\deProfessori\.config\opencode\AGENTS.md
```

**Expected:**
- Agent acknowledges project rules loaded
- Subsequent behavior reflects AGENTS.md content

**Pass criteria:** Rules imported, no error.

---

## Test 26: Ponytail Mode — Minimal Diff & Transparency Footer

**Prompt:**
```
SP ponytail full
Refactor the add function in utils.py to support variable args.
```

**Expected:**
- Smallest possible diff: `def add(*args): return sum(args)`
- Zero unrequested wrappers, helper functions, or classes
- Mandatory 1-2 line closing note detailing what was skipped and unverified risks

**Pass criteria:** Smallest complete change with closing transparency note.

---

## Test 27: Repo Fact Bank — Micro-Skills Harvesting

**Prompt:**
```
SP fact set test_cmd "pytest -m unit"
SP fact list
```

**Expected:**
- Fact stored: `test_cmd` = `"pytest -m unit"`
- Fact listed under verified repository facts

**Pass criteria:** Key/value fact persists and displays cleanly.

---

## Test 28: Model Tier Triage — Task Grading & Routing

**Prompt:**
```
SP tier-check "Audit the concurrent lock contention in the raft consensus module"
```

**Expected:**
- Output identifies task as `T3 (Hard)`
- Recommends flagship/reasoning model tier

**Pass criteria:** Accurate classification of hard architecture/concurrency tasks.

---

## Test 29: Caveman Dialect — Extreme Quota Compaction

**Prompt:**
```
SP caveman on
Explain what a deadlock is.
```

**Expected:**
- Ultra-dense telegraphic explanation with zero conversational filler
- Retains 100% technical correctness in < 25 words

**Pass criteria:** Concise, high-density dialect with no fluff.

---

## Scoring

| Category | Tests | Weight |
|---|---|---|
| Core memory (0, 13-15) | 5 | Critical |
| Lean mode (1-2) | 2 | High |
| Token budget (3-4) | 2 | Critical |
| Routing (5-6) | 2 | High |
| Opt-in helpers (7-12, 16-18, 21-25) | 13 | Medium |
| Guardrails (11-12) | 2 | Critical |
| Discovery (19-20) | 2 | Medium |

**Pass threshold:** 100% on Critical, ≥80% on High, ≥60% on Medium.

---

## Running Automated (for agents that can script)

```bash
# Pseudo-code for automation
for test in tests:
    reset_conversation()
    send_prompt(test.prompt)
    output = get_response()
    assert test.expected in output or test.predicate(output)
```

---

## Known Limitations (Expected Failures)

| Test | Reason |
|---|---|
| 7, 8, 16, 17, 18, 21-25 | Require storage adapter — will work in simulation but not persist without adapter |
| 22, 23 | Require multi-model host — simulated only |
| 24 | Requires index storage — simulated only |

These are **not failures of the skill** — they require the host agent to implement the adapter interface. See `STORAGE_ADAPTERS.md`.