---
name: deploy-check
description: Use before deploying to any environment, when the user says 'ready to ship', 'can we deploy', 'let's release', or to gate a CI/CD pipeline.
---

# Deploy check

Run this before deploying to any environment. The goal is to catch objective blockers — red CI, unresolved change requests, open release-blocker issues — before they become incidents. A reviewer's "LGTM" is not enough; CI, reviews, and open blockers are independent gates.

## Step 1 — CI status

Check whether all checks on the current branch/PR are green.

If on a PR branch:
```
gh pr checks
```

If not on a PR (e.g., direct branch push):
```
gh run list --branch $(git branch --show-current) --json status,conclusion --limit 1
```

**Rule:** Any check in a non-success state is a **HOLD**. List the specific failing check names. Do not proceed until CI is all-green.

## Step 2 — Blocking reviews

```
gh pr view --json reviewDecisions,reviews
```

Scan for any review with state `CHANGES_REQUESTED`. If the same reviewer has since approved, the block is lifted — check the timeline.

**Rule:** Any unresolved `CHANGES_REQUESTED` review is a **HOLD**. Name the reviewer and the outstanding concern if visible.

## Step 3 — Release blockers

```
gh issue list --label release-blocker --state open
```

If `gh` is not available or the repo does not use that label convention, note that this step could not be verified and flag it as manual.

**Rule:** Any open issue tagged `release-blocker` is a **HOLD**. List each issue by number and title.

## Step 4 — Migration risk

Inspect the diff for database migration files:

```
git diff --name-only main...HEAD | grep -E "(migrations/|migrate_|alembic/|\.migration\.ts)"
```

(Adjust the base branch if the default is not `main`.)

If migration files are present, add this manual verification checklist:

- [ ] Migration has been tested against a copy of production data or a realistic staging dataset
- [ ] Migration is reversible (down/rollback path exists and has been verified)
- [ ] Estimated runtime is known and acceptable for the deployment window
- [ ] Rollback plan is documented if migration cannot be reversed automatically

**Rule:** Migrations do not automatically block deployment, but they escalate the verdict to at least **CAUTION** and require the checklist above to be confirmed before a **GO**.

## Step 5 — Confirm deployment target

If the deployment target is not already clear from context, ask before issuing a verdict:

- Which environment? (staging / production / other)
- Which service or component is being deployed?
- What approval gates exist? (e.g., change-management ticket, on-call sign-off, maintenance window)

Do not assume production when staging is possible. Do not assume staging when the user says "ship it."

## Step 6 — Verdict

Issue exactly one of the following verdicts, followed by a specific list of evidence:

**GO** — All of the following are true:
- CI is all-green
- No unresolved `CHANGES_REQUESTED` reviews
- No open `release-blocker` issues
- If migrations are present, all checklist items are confirmed
- Deployment target and approval gates are known

**CAUTION** — Deployment can proceed with awareness, but note the specific condition:
- A migration is present and tested, but runtime or rollback risk is non-trivial
- A non-blocking review comment exists that the author has acknowledged
- CI passed but one check was skipped (e.g., an optional job)

**HOLD** — Do not deploy until the specific blocker is resolved:
- One or more CI checks are red or did not run — list them
- One or more `CHANGES_REQUESTED` reviews are unresolved — name the reviewer
- One or more `release-blocker` issues are open — list them by number and title

## Output

Report back with:
- The result of each step (pass / fail / caution / could-not-verify)
- For any failure or caution: the specific file, check name, issue number, or reviewer
- The final verdict: **GO**, **CAUTION**, or **HOLD**
- For **HOLD**: a short, numbered list of what must be resolved before retrying
