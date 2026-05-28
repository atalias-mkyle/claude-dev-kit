---
description: Run a security review on the current branch or a given PR
---

Use the `security-review` skill to review changes for security issues.

If a PR number was provided (e.g., `/security-check 123`), fetch the diff with `gh pr diff 123`.

Otherwise, get the current branch diff with `git diff $(git merge-base HEAD origin/main)..HEAD`.

If the diff is empty, tell the user there are no changes to review and stop.

Otherwise, invoke the `security-review` skill with the diff as context.
