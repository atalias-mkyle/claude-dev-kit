---
name: dependency-audit
description: Use when new dependencies have been added, before a release, when a security advisory mentions a package you use, or on a scheduled basis.
---

# Dependency audit

The goal is to surface actionable vulnerabilities before they ship. A vulnerability in a devDependency is not the same risk as one in a production code path — flag both, but distinguish them.

## Step 1 — Detect the package manager

Check for the presence of the following files in the repo root (more than one may exist in a monorepo — audit each):

- `package.json` → Node (npm or yarn)
- `requirements.txt` or `pyproject.toml` → Python
- `Cargo.toml` → Rust
- `go.mod` → Go
- `pom.xml` → Java (Maven)

If none are found, report that no supported package manifest was detected and stop.

## Step 2 — Run the appropriate audit tool

Run the command for each detected package manager. Capture the output.

**Node (npm)**
```
npm audit --json
```
If a `yarn.lock` is present and no `package-lock.json`, use:
```
yarn audit --json
```

**Python**
```
pip-audit -r requirements.txt --format json
```
If `pyproject.toml` is present instead, omit `-r requirements.txt` — pip-audit will detect it. If `pip-audit` is not installed: `pip install pip-audit`

**Rust**
```
cargo audit
```
If `cargo-audit` is not installed: `cargo install cargo-audit`

**Go**
```
govulncheck ./...
```
If `govulncheck` is not installed: `go install golang.org/x/vuln/cmd/govulncheck@latest`

**Java (Maven)**
```
mvn dependency-check:check
```

If a tool is unavailable and cannot be installed, note it clearly and skip that ecosystem rather than failing silently.

## Step 3 — Parse and filter

From the raw audit output:

- Extract each vulnerable package: name, installed version, patched version (if any), CVE or advisory ID, severity.
- For Node: check whether the vulnerable package appears only under `devDependencies` in `package.json`. If so, label it `dev-only`.
- A `dev-only` vulnerability is lower urgency — flag it but do not let it alone trigger ACTION REQUIRED.
- If a package is transitive (not directly in the manifest), note `transitive` so the fix strategy is clear.

## Step 4 — Group by severity

Sort all findings into buckets, highest first:

1. CRITICAL
2. HIGH
3. MEDIUM
4. LOW
5. INFO

## Step 5 — Detail each CRITICAL and HIGH finding

For every CRITICAL or HIGH severity finding, provide:

- **Package**: name (and ecosystem if a monorepo)
- **CVE / Advisory**: the ID (e.g., CVE-2024-12345 or GHSA-xxxx-yyyy-zzzz)
- **Installed version**: what is currently locked
- **Patched version**: the earliest version that resolves it, or "no fix available"
- **Mitigation**: the recommended action — upgrade, pin to a safe version, replace the package, or apply a workaround if no fix exists

## Output

Print a compact table covering all findings:

| Package | Installed | Patched | CVE / Advisory | Severity | Scope | Action |
|---------|-----------|---------|----------------|----------|-------|--------|
| example | 1.2.3 | 1.2.4 | CVE-2024-00001 | HIGH | prod | Upgrade |
| devtool | 0.9.0 | none | GHSA-aaaa-bbbb | MEDIUM | dev-only | Review |

Columns:
- **Scope**: `prod`, `dev-only`, or `transitive`
- **Action**: `Upgrade`, `Pin`, `Replace`, `Review`, or `No fix — monitor`

If there are no findings, print "No vulnerabilities found."

## Verdict

End with exactly one of the following verdicts:

**CLEAN** — No vulnerabilities found, or only INFO-level findings. No action required.

**ADVISORY** — Only MEDIUM or LOW findings, none in production code paths. Review at your discretion; not blocking for merge or release.

**ACTION REQUIRED** — One or more HIGH or CRITICAL findings present in production code paths. Resolve before merging or releasing. List the blocking packages explicitly.

If HIGH/CRITICAL findings exist but are all `dev-only`, downgrade to ADVISORY and note that explicitly.
