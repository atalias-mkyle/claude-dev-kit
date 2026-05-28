---
name: incident-response
description: Use when something broke after a deploy, a production incident is active, or a rollback needs to be evaluated quickly.
---

# Incident response — revert and verify

**Scope boundary.** This skill covers one thing: deciding whether to revert, generating the revert, and confirming recovery. It stops at "the system is stable again." Root cause analysis — why the bug existed, what the code should have done — belongs to the `debug-playbook`. Do not mix the two during an active incident. Stabilize first, understand second.

## Step 1 — Gather symptoms

Before touching git, ask the user the three questions. Don't proceed until you have answers to all three.

1. **What is broken?** (error message, metric spike, user-facing behavior — be specific)
2. **When did it start?** (approximate time, or "right after the deploy at HH:MM")
3. **What was deployed closest to that time?** (PR number, branch name, deploy pipeline ID — whatever is available)

If the user doesn't know what was deployed, that's fine — you'll find it in Step 2. But you need the symptom and the time before proceeding.

## Step 2 — Identify the suspect commit

Run the following, adjusting `--since` to match the symptom window:

```
git log --oneline --since="24 hours ago"
```

If the incident window is narrower (e.g., "it broke 20 minutes ago"), tighten the window. If it's a long-lived system with infrequent deploys, widen it.

Read the output. The suspect commit is the one deployed closest to — and before — the symptom start time. If multiple commits landed in one deploy, treat the entire batch as the suspect.

Note the SHA(s).

## Step 3 — Scope the blast radius

Run:

```
git show <suspect-sha> --stat
```

For each changed file, answer:
- Is this a schema migration or database DDL?
- Does this write data to an external system (queue, object store, third-party API)?
- Does a dependent service pin to this contract (shared library version, API shape)?

Write down the answers. You need them for Step 4.

If the commit batch is large, run `git show <sha> --stat` on each commit individually.

## Step 4 — Assess revert safety

**STOP and escalate (do not proceed to Step 5) if any of the following are true:**

- The commit includes a DB migration. Data may already be written in the new schema. Rolling back the code without rolling back the schema will likely cause data corruption or application errors worse than the current incident.
- The commit wrote data to an external system that cannot be un-written (sent emails, charged a card, pushed a message to a queue that's already been consumed).
- Rolling back would create a version mismatch with a dependent service that has already been updated to expect the new contract.

If you stop here, your output to the user should be:

> "This commit cannot be safely auto-reverted because [specific reason]. Escalate to an engineer with production DB / external-system access. The safe path forward is [migration rollback procedure / compensating write / service coordination], not a code revert."

If none of the blockers apply, proceed to Step 5.

## Step 5 — Generate the revert

Produce the command for the user. Do not run it yourself.

```
git revert <suspect-sha> --no-edit
```

If the suspect is a merge commit, you'll need `--mainline 1`:

```
git revert <suspect-sha> --mainline 1 --no-edit
```

Then produce a draft PR description for the human to review and edit before pushing:

---

**Title:** `revert: <original commit subject line>`

**Body:**

```
Reverts <suspect-sha>.

Reason: <one sentence describing the symptom>

Safe to revert: <yes — no migrations or external writes involved>

What this revert does NOT fix: root cause is unknown; this only removes the most recent change to stop the bleeding. Follow up with debug-playbook once the system is stable.

Monitoring after merge: <see Step 6 checklist>
```

---

Present this draft to the user and wait for approval. Do not push or merge.

## Step 6 — Post-revert monitoring checklist

After the revert is merged and deployed, confirm recovery by watching the following. Present this checklist to the human doing the deploy.

- [ ] **Primary symptom resolved:** [restate the symptom from Step 1]
- [ ] **Observation window:** watch for at least 5 minutes after deploy before declaring resolved; for low-traffic systems, extend to 15-30 minutes
- [ ] **Secondary symptoms:** check adjacent metrics (latency p99, queue depth, downstream error rates)
- [ ] **Who to notify:** the on-call engineer, the team that owns the service, and whoever reported the incident

Once all checklist items are confirmed green, close the incident and hand off to `debug-playbook` for root cause analysis.

## Anti-patterns to avoid

- **Auto-applying the revert.** You must present the command and PR draft for human approval. The human presses the button.
- **Skipping the blast-radius check.** The most dangerous reverts are the ones that look safe. Always run `git show --stat`.
- **Conflating stabilization with root cause.** Once the system is stable, resist the urge to investigate why inline. Open a separate thread, use `debug-playbook`, and do it with a cool head.
- **Reverting multiple commits at once without checking each.** Each commit in a batch may have a different safety profile. Check them individually.
