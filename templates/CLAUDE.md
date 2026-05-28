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
- After planning, validate with the `reverse-reasoner` subagent before saying "go" — it traces the plan forward and backward to surface gaps before code is written.
- Run tests via the `test-runner` subagent rather than dumping output here.
- For library APIs, prefer Context7 over guessing from training data.
- Before opening a PR, run `/pr-check`.
- When a significant architectural decision is made (choosing X over Y, deciding on an approach), record it in `.claude/memory/decisions.md`.
- When the user expresses a preference about how to work (verbosity, library choices, conventions), record it in `.claude/memory/preferences.md`.
- Before each step of implementation, write a brief note to `.claude/memory/session-state.md` so the next agent has context.

## Workflow State
- In-progress work: `.claude/workflow-state.json` (written by implementer, read at session start)
- Inter-agent handoff: `.claude/memory/session-state.md` (planner/implementer write brief handoff notes here)
- Architectural decisions: `.claude/memory/decisions.md` (appended automatically at session end)
- User preferences: `.claude/memory/preferences.md` (Claude records preferences here when the user expresses them)

## Behavioral guidelines

**Think before coding.** State assumptions explicitly. If multiple interpretations exist, present them — don't pick silently. If something is unclear, stop and ask.

**Simplicity first.** Minimum code that solves the problem. No features beyond what was asked. No abstractions for single-use code. If you write 200 lines and it could be 50, rewrite it.

**Surgical changes.** Touch only what you must. Don't "improve" adjacent code or formatting. Match existing style. Every changed line should trace directly to the request.

**Goal-driven execution.** Transform tasks into verifiable goals: "fix the bug" → "write a test that reproduces it, then make it pass." For multi-step work, each step ends with a concrete verify check.

## What this file should NOT contain
- Long architectural narratives — those live in `.claude/memory/decisions.md`.
- Step-by-step procedures — those belong in a skill under `.claude/skills/`.
- Anything that goes stale within a sprint — keep this file pointing to where the truth lives, not being the truth.
