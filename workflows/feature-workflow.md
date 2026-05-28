# Feature Workflow

## When to use this

- New feature development
- Changes touching 3+ files or requiring a design decision
- NOT for bug fixes (use `workflows/hotfix-workflow.md`)

---

## Pre-flight

- [ ] Branch created from `main`
- [ ] `CLAUDE.md` exists in project root (if not: run `/bootstrap`)
- [ ] `.claude/workflow-state.json` cleared from any prior run

---

## Stage 1 — Research (`researcher` agent)

**Invoke:** Describe what you need to build and ask the researcher to map affected systems.

**Expected output:**
- List of affected files and modules
- Unfamiliar API or library findings (sourced from context7 or brave-search)
- Relevant prior decisions from `.claude/memory/decisions.md`

**Proceed when:** Researcher returns a clear scope with no unresolved unknowns.

> If the scope is ambiguous after research, stop and clarify with the human before proceeding.

---

## Stage 2 — Plan (`planner` agent)

**Invoke:** Give the planner the research output plus the original task description.

**Expected output:**
- Ordered step list with stable IDs (e.g., `STEP-1`, `STEP-2`, ...)
- Estimated file changes per step
- Any explicit dependencies between steps
- Parallel streams identified if non-overlapping file sets exist (see [Parallel work streams](#parallel-work-streams))

**Proceed when:** The plan looks reasonable and all steps are traceable to the task. Ask for revisions if any step is vague or the scope has crept.

---

## Stage 3 — Validate (`reverse-reasoner` agent)

**Invoke:** Give the reverse-reasoner the plan from Stage 2.

**Expected output:**
- Forward-pass analysis: does the plan's happy path hold end-to-end?
- Backward-pass precondition check: what must be true for the final state to be valid?
- Gap list: missing steps, unmet preconditions, or unstated assumptions

**If blockers found:** Loop back to Stage 2 with the gap list as new constraints (max 2 re-plans).

**Proceed when:** No blockers remain, or all remaining blockers are acknowledged risks that the human accepts.

---

## Stage 4 — HUMAN GATE

Review the validated plan in full.

- Type **`go`** to proceed to implementation.
- Or request specific changes — loop back to Stage 2 or Stage 3 as appropriate.

> This is the last easy stop before code is written. Take it seriously.

---

## Stage 5 — Implement (`implementer` agent)

**Invoke:** Give the implementer the validated plan (with step IDs intact).

**During execution:**
- Implementer writes `.claude/workflow-state.json` after completing each step.
- Each write records: step ID, status, files changed, and any deferred decisions.

**Expected output at completion:**
- `status`: `complete` | `partial` | `blocked`
- `steps_completed`: list of step IDs finished
- `files_changed`: list of modified/created files

**If `partial` or `blocked`:** See `workflows/recovery-playbook.md` before retrying.

---

## Stage 6 — Test (`test-runner` agent)

**Invoke:** No special arguments needed — the test-runner reads the codebase and runs the relevant test suite.

**On failures:**
- Route the full failure output back to the implementer with the specific failing tests.
- Max 3 fix-and-retest attempts before escalating.

**If still failing after 3 attempts:** STOP. Present the failure output to the human and do not proceed to review.

---

## Stage 7 — Review (`reviewer` agent)

**Expected output — one of four verdicts:**

| Verdict | Action |
|---|---|
| `ship` | Proceed to Stage 8 or Stage 9 |
| `ship with nits` | Proceed to Stage 8 or Stage 9; nits are informational |
| `needs changes` | Return to implementer with reviewer's specific change requests |
| `block` | Return to Stage 2 with blocking reasons as new constraints |

> For `needs changes` loops: track the iteration count. After 2 loops without resolution, escalate to the human.

---

## Stage 8 — Security Review (`security-reviewer` agent) — conditional

**Invoke only if changes touch any of:**
- Authentication or authorization logic
- User input handling or validation
- External API calls
- File I/O or shell command execution
- Infrastructure configuration

**Expected verdicts:**

| Verdict | Action |
|---|---|
| `PASS` | Proceed to Stage 9 |
| `WARN` | Document findings in `.claude/memory/decisions.md`, proceed with acknowledgment |
| `BLOCK` | Return to implementer with specific findings; do not ship until resolved |

> The security-reviewer has no write access. All remediation is done by the implementer.

---

## Stage 9 — Complete

- [ ] Create PR using `/pr-check`
- [ ] Run `memory-curator` agent if significant architectural decisions were made during this workflow
- [ ] Clear `.claude/workflow-state.json` (or leave it — `session_context.py` reads it at next SessionStart and will surface it)

---

## Parallel work streams

If the plan contains non-overlapping file sets (e.g., frontend and backend with no shared files):

1. **Planner** must explicitly label streams (e.g., `stream: frontend`, `stream: backend`) and assign each file to exactly one stream.
2. **Reverse-reasoner** must verify there are no shared writes across streams before approving the plan. If shared writes exist, the streams are not truly parallel — merge them.
3. **Spawn separate implementer calls per stream.** Each implementer writes its own `workflow-state.json` section keyed by stream name.
4. **Test-runner and reviewer run once after all streams complete,** not per-stream.

---

## Failure recovery

See `workflows/recovery-playbook.md` for:
- Partial implementation recovery
- Blocked implementer escalation
- Test loops that don't converge
- Re-plan procedures after a blocking review
