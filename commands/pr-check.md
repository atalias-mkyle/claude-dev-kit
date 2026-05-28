---
description: Run the pre-PR self-review checklist before pushing
---

Use the `pr-checklist` skill to do a pre-PR self-review of the current branch's changes.

Determine the base branch (usually `main` or `master`; if neither exists, ask). Run the checklist against `git diff <base>...HEAD`. Hand the test step to the `test-runner` subagent so the output stays compact.

Return the checklist results and a drafted PR description, ready for the user to paste.
