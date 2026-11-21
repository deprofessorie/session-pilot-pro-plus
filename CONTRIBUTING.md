# Contributing to Session Pilot Pro Plus

Thanks for caring about token efficiency and agent memory! This doc is intentionally short — we value your time.

---

## First Things First

1. **Fork** this repo → `git clone` the fork locally.
2. Install Python 3.10+ (the skill and all adapters are stdlib-only).
3. Run the baseline verification:
   ```bash
   python scripts/verify.py --adapter json_file
   python scripts/verify.py --adapter sqlite
   ```
   Both must pass before we merge anything.

---

## Adding a New Capability

Every new command or feature follows this contract:

```markdown
## New-Feature Section (always insert between existing sections)

### Feature Name (`SP command [--flag]`)
- One-sentence description of what it does.
- When to use: <scenario>
- Token cost estimate: ~X tokens on invoke, saves ~Y tokens per turn.
- Storage needed: no / adapter-backed (JSON file, SQLite, etc.)
- Example:
  ```text
  SP command --flag "value"
  ```
```

Then update:
- `session-pilot-pro_SKILL.md` — add to Core or Optional list
- `README.md` — add to Command reference table
- `EVALUATION.md` — add a test case (section "Test N")
- `COMPATIBILITY.md` — mark support level per agent

---

## Adding a Storage Adapter

Adapters live in `adapters/`. The interface is defined in `STORAGE_ADAPTERS.md`. Requirements:

1. Implements all methods from the `StorageAdapter` protocol (see that file).
2. Passes every test in `scripts/verify.py` with `--adapter <your-name>`.
3. Has a one-line usage example at the bottom of its file:
   ```python
   # Usage: SESSION_PILOT_HOME=/data/python scripts/verify.py --adapter your_name
   ```
4. File name convention: `your_name.py` (lowercase, underscores only).

After adding, update `STORAGE_ADAPTERS.md`'s built-in adapters section and `COMPATIBILITY.md`.

---

## Documentation Standards

- Keep sentences under 25 words.
- Every code block must be copy-paste runnable.
- Link to related docs (e.g., "See `STORAGE_ADAPTERS.md` for implementation details").
- Version bumps go in frontmatter only; do not hardcode versions elsewhere.

---

## Testing Before Submitting

Run the full suite locally first:
```bash
python scripts/verify.py --adapter json_file
python scripts/verify.py --adapter sqlite
python scripts/repl.py  # manual smoke-test
docker build -t sp-test . && docker run --rm sp-test python scripts/verify.py
```

GitHub Actions will re-run everything automatically — but fixing it locally first respects everyone's CI minutes.

---

## Token Budget Rule

If a new feature adds >50 tokens to the core prompt (not counting opt-in helpers), it needs a justification comment in the PR explaining why the trade-off is worth it. Core prompt stays at **~180 tokens**.

---

## License

By contributing, you agree to license your additions under MIT. No CLA required.
