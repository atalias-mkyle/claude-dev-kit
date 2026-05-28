# Hotfix Workflow

## When to use vs feature-workflow

Use this when ALL of the following are true:

- Single root cause already identified (or likely to be found quickly)
- Change scope is <= 3 files, <= 50 lines
- No new abstractions or APIs being introduced
- Urgency matters (production bug, blocking issue)

If any of these is false, use [feature-workflow.md](feature-workflow.md) instead.

---

## Pre-flight

- [ ] Hotfix branch: `git checkout -b fix/<short-description>`
- [ ] Exact error message or failing test in hand

---

## Stage 1 — Debug (`debugger` agent)

**Invoke:** Give the exact error message, stack trace, or failing test name.

**Agent:** `agents/debugger.md` — sonnet, diagnostic tools only (no writes).

**Expected output:**
- Root cause (one sentence)
- Fix description (exact file + line)
- Evidence (log excerpt, symbol trace, or failing assertion)

**Gate:** If debugger cannot reproduce the issue or returns "inconclusive" — STOP. This is not a hotfix. Switch to [feature-workflow.md](feature-workflow.md).

---

## Stage 2 — Implement (`implementer` agent)

**Invoke:** Pass the debugger's output only. No planner step is needed for hotfixes.

**Agent:** `agents/implementer.md` — sonnet, full write/edit access + serena MCP.

**Expected output:**
- `Status: complete`
- 1–3 files changed, <= 50 lines total
- `.claude/workflow-state.json` updated

**Gate:** If `Status: partial` (touched unexpected files) or `Status: blocked` (missing context) — STOP immediately. The fix is more complex than it appeared. Escalate to [feature-workflow.md](feature-workflow.md). Do not attempt to patch around the blocker.

---

## Stage 3 — Test (`test-runner` agent)

**Invoke:** Run the existing test suite plus any tests that directly cover the changed code.

**Agent:** `agents/test-runner.md` — haiku, read + bash only.

**ZERO RETRY POLICY:** If tests fail on the first run, do not loop, do not ask the implementer to patch again. Escalate to [feature-workflow.md](feature-workflow.md).

Hotfixes must pass on first attempt. A fix that requires iterative test repair is not a hotfix.

---

## Stage 4 — Review (`reviewer` agent)

**Invoke:** Pass the diff and the debugger's root-cause statement.

**Agent:** `agents/reviewer.md` — sonnet, read-only.

**Outcomes:**

| Verdict | Action |
|---|---|
| `ship` | Proceed to Stage 5 immediately |
| `ship-with-nits` | Proceed to Stage 5; nits deferred to follow-up |
| `needs-changes` | STOP — escalate to feature-workflow.md |
| `block` | STOP — escalate to feature-workflow.md |

Do not accept a reviewer-blocked hotfix just because it is urgent. A blocked hotfix merges risk, not speed.

---

## Stage 5 — Deploy check (`/deploy-check` skill)

**Invoke:** `/deploy-check`

**Checks performed by the skill:**
- CI is green on the hotfix branch
- No unresolved blocking review comments
- Branch is up to date with the merge target

Do not merge until this step is clean.

---

## Complete

1. Merge — squash merge preferred for hotfixes (keeps main history readable)
2. Tag if this constitutes a patch release (e.g. `v1.4.1`)
3. Monitor for 30 minutes post-deploy (error rate, relevant metrics, alerting channels)
4. File a brief follow-up ticket if the root cause points to a broader systemic issue

---

## Escalation rule

> If at any stage the scope expands beyond the original root cause, stop and switch to [feature-workflow.md](feature-workflow.md).

Specific triggers:

- **Stage 1:** Debugger cannot reproduce or root cause is ambiguous
- **Stage 2:** Implementer touches files outside the identified root cause, or reports blocked
- **Stage 3:** Tests fail on first run
- **Stage 4:** Reviewer returns `needs-changes` or `block`

Speed pressure is not a reason to skip escalation. An unreviewed or partially-tested fix in production is worse than a delayed one.

---

## Agent pipeline summary

```
debugger → implementer → test-runner → reviewer → /deploy-check
```

Skipped from the full pipeline: researcher, planner, reverse-reasoner, security-reviewer (unless the fix touches auth/crypto — in that case, insert security-reviewer between reviewer and deploy-check).
