---
name: onboard
description: Use when onboarding a new team member, starting work after a long break, or when asked "how do I get started" or "what's the state of this project".
---

# Project onboard

Produce a one-page state-of-the-union for someone new to this project or returning after a long break. The goal is orientation — a map, not a manual.

This skill is **read-only**. It does not create, edit, or delete any files.

## Data gathering

Collect all of the following. If a source is missing, skip it and note the gap.

1. **`CLAUDE.md`** — project overview, commands, conventions. Read from the project root.

2. **`.claude/memory/decisions.md`** — architectural decisions. Read the last 5 entries only.

3. **Recent git activity** — run:
   ```
   git log --oneline -15
   ```

4. **Open issues** — if `gh` is available, run:
   ```
   gh issue list --limit 8 --state open --json number,title,labels
   ```
   If `gh` is not available or the repo has no remote, skip silently.

5. **Open PRs** — if `gh` is available, run:
   ```
   gh pr list --limit 5 --state open --json number,title,author
   ```
   Skip silently if unavailable.

6. **Top-level directory listing** — list the project root, excluding `node_modules`, `.git`, and `.claude`. Use this to understand broad layout (src vs app vs lib, presence of docs/, scripts/, etc.).

## Output structure

Write the report directly in chat. Keep it to roughly one screen. Use this structure exactly:

---

## What this project does
One or two sentences drawn from CLAUDE.md. If CLAUDE.md is missing, infer from the repo name and directory layout and label it as inferred.

## Getting it running
The install, dev, and test commands from CLAUDE.md's Commands section. If any command is marked TODO or missing, call that out explicitly so the reader knows to ask.

## Recent activity
The last 10 commits, one line each. Don't recite the raw hash and message — paraphrase the intent in a few words. Group related commits if there are obvious clusters (e.g., "3 commits fixing the auth flow").

## Open issues
The top 5 open issues by number, with title. If there are labels, note them. If there are none, say so.

## Open PRs
The top 3 open PRs with title and author. If there are none, say so.

## Key decisions
The last 3 entries from `.claude/memory/decisions.md`, one sentence each summarizing the decision (not the full context). If the file doesn't exist, say so and suggest running `/bootstrap` to create it.

## Good entry points
Three to five files a newcomer should read first. Infer from CLAUDE.md's Architecture pointers section and the directory listing. Typical candidates: main entry point, primary config file, one representative test. Give the path and one sentence on why it's worth reading.

---

## What not to do

- Don't invent information. If a source is missing, say "not found" and move on.
- Don't dump raw `git log` output. Summarize it.
- Don't read the entire codebase. The directory listing and CLAUDE.md are enough to identify entry points.
- Don't suggest changes or improvements. This is orientation only.
- Don't ask clarifying questions before running. Just gather and report.

## If CLAUDE.md doesn't exist

Note it prominently at the top of the report: the project hasn't been bootstrapped yet. Provide whatever you can infer from the directory listing and git history, then recommend running `/bootstrap` as the first real step.
