---
name: pr-checklist
description: Use before opening a pull request, when the user says "ready to ship", "let's PR this", "check before I push", or asks for a self-review pass. Walks through a pragmatic pre-PR checklist that catches the things reviewers always catch, so reviewers can focus on the things only humans catch.
---

# PR checklist

Run this before you put a PR up for human review. The point is not ceremony — it's that the reviewer's attention is a scarce resource, and you should not be spending it on `console.log` left in the diff.

## Step 1 — Read the whole diff yourself

Run `git diff <base>` and read every hunk. You'll catch about half of the issues a reviewer would, just by reading them in a different mental mode than you wrote them.

## Step 2 — Commit history

Run the `conventional-commits` skill to audit every commit on this branch. Flag any that are vague, wrongly cased, or missing a type prefix. Surface reword suggestions before continuing.

## Step 3 — Mechanical sweep

Run through this list; mark each `pass`, `fail`, or `n/a`:

- [ ] No debug prints, `console.log`, `dbg!`, `pp`, `print()`, etc. left in
- [ ] No commented-out code blocks more than 2 lines
- [ ] No `TODO` / `FIXME` you don't intend to fix in a follow-up issue
- [ ] No secrets, API keys, real customer data, or internal URLs
- [ ] No `.env`, `.DS_Store`, `__pycache__/`, `node_modules/`, build artifacts
- [ ] Generated files (lockfiles, migrations) intentional and minimal
- [ ] New dependencies actually used and worth the cost
- [ ] All files touched have consistent indent/style with the rest of the repo
- [ ] Filenames and function names match the repo's naming convention

## Step 4 — Behavioral sweep

- [ ] Tests cover the new behavior, not just the function existing
- [ ] Tests cover at least one unhappy path (empty input, error, etc.)
- [ ] The full test suite passes (hand to `test-runner` subagent)
- [ ] If anything user-visible changed, the docs/changelog/readme reflect it
- [ ] If anything in the public API changed, callers were updated
- [ ] If anything DB-related changed, the migration is reversible

## Step 5 — PR description

Draft a description with:
- **What:** one or two sentences. Pretend the reviewer has never heard of this work.
- **Why:** link to the ticket / issue, or write the context if there isn't one.
- **How:** the approach, in two or three sentences. If the approach was non-obvious, this is the most valuable section.
- **Testing:** what you ran, what you verified manually.
- **Risk / rollout:** anything to watch after merging.

## Step 6 — Decide if it's actually ready

If you'd be embarrassed to point a reviewer at it, it's not ready. The fix is usually small and obvious — do it now, not after the review round-trip.

## Output

Report back:
- Items that passed
- Items that failed (with the specific file:line)
- Items you couldn't check and why
- Whether the PR is ready or what blocks it
- The drafted PR description, ready for the user to paste
