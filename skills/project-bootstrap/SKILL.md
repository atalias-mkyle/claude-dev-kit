---
name: project-bootstrap
description: Use when the user wants to set up Claude Code on a new project, asks to "create a CLAUDE.md", "bootstrap claude", "initialize claude for this repo", or when there is no CLAUDE.md in the current project root yet and the user is starting work. This skill drops in a small, project-specific CLAUDE.md based on what's actually in the repo, and creates a `.claude/memory/decisions.md` for architectural decisions.
---

# Project bootstrap

Set up Claude Code for the current project. The output is intentionally small — a CLAUDE.md under ~500 tokens is better than one that drifts and goes stale.

## Steps

1. **Detect the stack.** Read the repo root and look at:
   - `package.json` → Node/JS/TS
   - `pyproject.toml` / `requirements.txt` / `setup.py` → Python
   - `Cargo.toml` → Rust
   - `go.mod` → Go
   - `Gemfile` → Ruby
   - `pom.xml` / `build.gradle` → JVM
   - `composer.json` → PHP
   List the top 3 languages by file count if it's a polyglot.

2. **Find the canonical commands.**
   - Build / dev: from `package.json` scripts, Makefile, `pyproject.toml`, etc.
   - Test: same sources.
   - Lint / format: same.
   If you can't find them, leave a TODO marker rather than inventing.

3. **Identify obvious conventions** by reading 2-3 representative source files: indentation, naming, test layout, where types live, where utilities live. Keep this to 3-5 bullet points.

4. **Write `CLAUDE.md` at the project root.** Use this template, filling in only what you can verify. Delete sections that don't apply.

   ```markdown
   # CLAUDE.md — <project name>

   ## What this is
   <one sentence>

   ## Commands
   - Install: <cmd>
   - Dev: <cmd>
   - Test: <cmd>
   - Lint / format: <cmd>

   ## Conventions
   - <bullet 1>
   - <bullet 2>
   - <bullet 3>

   ## Architecture pointers
   - Entry point: `<path>`
   - Tests live in: `<path>`
   - Shared utilities: `<path>`
   - Architectural decisions: see `.claude/memory/decisions.md`

   ## Working agreements
   - Plan before implementing for any change touching more than one file.
   - Run tests via the `test-runner` subagent rather than dumping output here.
   - For library APIs, prefer Context7 over guessing from memory.
   ```

5. **Create `.claude/memory/decisions.md`** if it doesn't exist, with a header and one example entry so the format is clear:

   ```markdown
   # Architectural decisions

   ## YYYY-MM-DD — <decision title>
   **Context:** what forced the decision
   **Decision:** what we chose
   **Rejected alternatives:** with one-line reason each
   **Consequences:** what this locks us into
   ```

6. **Report back** in chat:
   - What was created and where
   - Anything that needs the user's input (commands you couldn't auto-detect)
   - Suggested next step (usually: review CLAUDE.md and adjust)

## What not to do

- Don't write more than ~500 tokens in CLAUDE.md. If it's getting long, you're putting procedure where a skill belongs.
- Don't list every file in the repo. Pointers, not inventory.
- Don't invent commands. If you can't find a test runner, write `Test: <TODO: add command>` and move on.
- Don't overwrite an existing CLAUDE.md without asking.
