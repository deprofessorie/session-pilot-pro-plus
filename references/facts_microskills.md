# Repository Micro-Skills & Fact Bank

> Mechanism Classification:
> - **Fact Bank Storage:** ● Enforced natively via JSON file / SQLite WAL store.
> - **Auto-Harvesting Hook:** ● Enforced natively via `hooks/post_tool_use.py` (Claude Code `PostToolUse` Bash matcher) and `sp.py harvest`.
> - **Manual Curation:** ● Enforced natively via `sp.py fact set/get/list/delete`.

---

## 1. Purpose
Agents waste 18–31% of exploration tokens repeatedly discovering how a repository builds, tests, or formats. Session Pilot Pro Plus captures these facts once and reloads them on recall.

---

## 2. Automatic Fact Harvesting (`PostToolUse`)

When configured with Claude Code hooks (`python hooks/install_hooks.py`), the `PostToolUse` hook listens to `Bash` command executions:
- **Test Commands:** Detects `pytest`, `vitest`, `jest`, `cargo test`, `go test`, `npm test`, `pnpm test`, `bun test`.
- **Build Commands:** Detects `pnpm build`, `npm run build`, `yarn build`, `cargo build`, `go build`, `mvn compile`, `gradle build`.
- **Package Managers:** Identifies `pnpm`, `yarn`, `bun`, `cargo`.
- **Linters:** Identifies `ruff`, `eslint`, `black`, `clippy`.

Facts are saved directly to `facts/<project>/<key>.json` without auxiliary LLM calls.

You can also trigger manual harvesting on a command string:
```bash
python scripts/sp.py harvest "pnpm run test:unit"
```

---

## 3. Manual Curation Commands

```bash
# Store a verified fact
python scripts/sp.py fact set test_cmd "pytest -m unit -q"
python scripts/sp.py fact set build_cmd "pnpm build"

# Retrieve or list facts
python scripts/sp.py fact get test_cmd
python scripts/sp.py fact list

# Delete obsolete fact
python scripts/sp.py fact delete test_cmd
```

---

## 4. Auto-Injection Protocol
On `sp.py recall`, verified repository facts are loaded into the turn context, preventing repetitive `ls`, `find`, `cat package.json`, and trial-and-error discovery turns.
