# CLAUDE.md — <project name>

## What this is
<One sentence so a stranger could understand the project's purpose.>

## Commands
- Install: <cmd>
- Dev: <cmd>
- Test: <cmd>
- Lint / format: <cmd>

## Conventions
- <Concrete bullet — e.g., "Tests live next to the file they test, named `*.test.ts`">
- <Concrete bullet — e.g., "Public API surface lives in `src/index.ts`; nothing else exports">
- <Concrete bullet — e.g., "Errors are values, not exceptions, in the `core/` layer">

## Architecture pointers
- Entry point: `<path>`
- Tests live in: `<path>`
- Shared utilities: `<path>`
- Architectural decisions: see `.claude/memory/decisions.md`

## Working agreements
- Plan before implementing for any change touching more than one file (use the `planner` subagent).
- Run tests via the `test-runner` subagent rather than dumping output here.
- For library APIs, prefer Context7 over guessing from training data.
- Before opening a PR, run `/pr-check`.

## What this file should NOT contain
- Long architectural narratives — those live in `.claude/memory/decisions.md`.
- Step-by-step procedures — those belong in a skill under `.claude/skills/`.
- Anything that goes stale within a sprint — keep this file pointing to where the truth lives, not being the truth.
