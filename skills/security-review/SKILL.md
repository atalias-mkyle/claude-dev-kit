---
name: security-review
description: Use when the user asks for a security review, security check, or wants to audit changes before merging — especially changes that touch auth, input handling, external API calls, file I/O, shell commands, or infrastructure configuration.
---

# Security review

If a `security-reviewer` subagent is available in the current context, invoke it and pass the diff. Otherwise, proceed inline with the steps below.

---

## Step 1 — Get the diff

Run `git diff <base>...HEAD` (or `git diff` for uncommitted changes). Read every hunk before forming opinions. Know what the change is trying to do before deciding whether it does it safely.

## Step 2 — Secret scan

Grep the diff for patterns that indicate hardcoded credentials. Flag any match:

- AWS access keys: `AKIA[0-9A-Z]{16}`
- OpenAI / Stripe / general `sk-` keys: `sk-[a-zA-Z0-9]{20,}`
- GitHub tokens: `ghp_[a-zA-Z0-9]{36}` or `github_pat_`
- Slack tokens: `xox[bpoas]-`
- Bearer tokens assigned inline: `Bearer [a-zA-Z0-9\-._~+/]{20,}`
- Password literals: `password\s*=\s*["'][^"']{4,}["']` (case-insensitive)
- Connection strings with embedded credentials: `://[^:]+:[^@]+@`

Any match is an automatic BLOCK regardless of what the other steps find.

## Step 3 — Dependency audit

Detect the stack from lockfiles or manifests, then run the appropriate audit command:

| Stack | Command |
|---|---|
| Node / npm | `npm audit --audit-level=high` |
| Node / yarn | `yarn audit --level high` |
| Python | `pip-audit --desc --fix-dry-run` |
| Rust | `cargo audit` |
| Go | `govulncheck ./...` |

Parse output for HIGH and CRITICAL severity only. Ignore LOW and MEDIUM in the verdict unless they are in the specific code path being changed. If the audit tool is not installed, note it and skip — do not block on a missing tool.

## Step 4 — Input tracing

For each new or modified function that accepts data from an external source (HTTP body, query param, form field, file upload, environment variable read at runtime, message queue payload):

- **Shell commands:** arguments are parameterized or escape-quoted — not string-interpolated from user input
- **SQL:** queries use `?`, `%s`, or named bind parameters — not f-strings or concatenation
- **HTML output:** values pass through an escape function (`html.escape`, `encodeURIComponent`, template auto-escaping) before rendering
- **File paths:** paths are constructed with `os.path.join` / `path.join` anchored to a known root, and traversal sequences (`../`) are rejected before use

Flag any location where user-controlled data reaches one of these sinks without going through the appropriate sanitizer.

## Step 5 — Auth and authz check

Scan new HTTP route handlers, RPC handlers, and GraphQL resolvers for:

- **Authentication:** middleware or decorator is present that requires a valid session or token before the handler executes; unauthenticated paths are explicitly marked, not the accidental default
- **Authorization:** operations that are scoped to a user or resource verify that the calling identity owns or is permitted on that resource — not just that they are logged in
- **JWT handling:** decode calls validate the signature (not `decode(token, options={verify: false})` or equivalent); algorithm is pinned, not accepted from the token header

## Step 6 — Insecure defaults

Check the diff for these specific patterns:

- External HTTP calls use `https://`, not `http://`
- Cryptographic operations use SHA-256 or stronger; MD5 and SHA-1 are not used for anything security-sensitive
- Password storage uses a password hashing function (bcrypt, argon2, scrypt) — not a plain hash
- Login, registration, and password-reset endpoints have rate limiting in place or an explicit note that it is handled upstream
- TLS verification is not disabled (`verify=False`, `InsecureSkipVerify: true`, `NODE_TLS_REJECT_UNAUTHORIZED=0`)

---

## Output

### Verdict

One of:

- **PASS** — no findings that require action before merging
- **WARN** — findings worth fixing but none meet BLOCK criteria
- **BLOCK** — one or more BLOCK-level findings; do not merge until resolved

### Findings

For each finding:

```
[SEVERITY]  category: short description
File: path/to/file.ext:line
Recommendation: specific fix
```

Severity levels: `CRITICAL` / `HIGH` / `MEDIUM` / `LOW` / `INFO`

### Dependency summary

One of:

- **CLEAN** — no advisories found
- **ADVISORY** — low or medium advisories only; note counts
- **ACTION REQUIRED** — high or critical CVE found; list each with CVE ID, package, and patched version if available

---

## BLOCK criteria

Issue an automatic BLOCK verdict if any of the following are true:

1. A hardcoded secret matching the patterns in Step 2 is present in the diff
2. User-controlled input reaches a shell, SQL, or HTML sink without sanitization (Step 4)
3. A HIGH or CRITICAL CVE exists in a dependency that is in the code path under review (Step 3)
4. JWT signature verification is skipped or algorithm is accepted from the token (Step 5)

A BLOCK is not a judgment call. If the criterion is met, the verdict is BLOCK.
