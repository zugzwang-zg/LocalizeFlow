# Open-source security patch candidate readiness

> Candidate: `v0.2.0-preview.2`
> Audit date: 2026-08-16
> Candidate state: release content ready; owner acceptance pending
> Formal release: not authorized before protected checks, protected merge, and
> `main` release smoke

## Recommendation

Publish `v0.2.0-preview.2` as a security-only prerelease and direct new users to
it. Keep `v0.2.0-preview.1` immutable for traceability; do not move or silently
replace its tag.

The portfolio product, evaluation, public Demo, and hosted-trial boundaries are
unchanged. The only runtime dependency update moves `cryptography` from 46.0.7
to 50.0.0, the highest first-patched version required by four newly reported
advisories.

## Detection and response

- GitHub created eight open Dependabot alert records after the first 0.2.0
  preview release. They represented four advisories duplicated across
  `pyproject.toml` and `uv.lock`: three High and one Medium.
- The earlier local audit completed before the new advisory records reached
  GitHub, which explains the conflicting time-of-check result.
- Dependabot PR #13 changed only `pyproject.toml`, `requirements.txt`, and
  `uv.lock`, and upgraded `cryptography` to 50.0.0.
- PR #13 passed Python 3.11/3.12/3.13, Web, and both CodeQL analyses. An
  independent Windows Python 3.12 environment repeated the full Python gate.
- After protected merge `d4af75bcc7c311bdc2d909a9e350e4a73ff01da8`,
  dependency-graph refresh reduced open Dependabot alerts from eight to zero;
  Code Scanning and Secret Scanning remained at zero.

## Addressed advisories

| Advisory | Severity | First patched version used |
|---|---|---:|
| GHSA-537c-gmf6-5ccf | High | 48.0.1 |
| GHSA-g6cj-pr64-35w5 | High | 50.0.0 |
| GHSA-jwv3-5hgf-82ww | High | 49.0.0 |
| GHSA-m2h6-j472-rp4c | Medium | 49.0.0 |

The candidate pins 50.0.0 and requires `cryptography>=50.0.0,<51` in both
requirement declarations.

## Verification results

| Gate | Result |
|---|---|
| Candidate decision | `RELEASE_READY`; formal release authorization remains false |
| Locked dependency | `cryptography==50.0.0` |
| Python tests | 141 passed plus 6 subtests |
| Python coverage | 72.22%, above the 70% threshold |
| Ruff / mypy | Passed |
| Prompt/schema validation | 6 schemas, 9 prompts, 0 API calls; passed |
| Startup smoke | Passed |
| Operations drill | Passed; recovered to healthy, no content bodies logged |
| Installed-environment audit | No known vulnerabilities |
| Merged security update CI | Passed on Python 3.11/3.12/3.13 and Web |
| Merged security update CodeQL | Python and JavaScript/TypeScript passed |
| GitHub open security alerts | Dependabot 0; Code Scanning 0; Secret Scanning 0 |

## Remaining release gate

1. Project owner accepts this security patch candidate and tag.
2. The final candidate PR head passes all protected CI/CodeQL checks.
3. The PR is merged without bypassing branch protection.
4. The exact merged `main` SHA passes manually dispatched `Release smoke`.
5. A new annotated `v0.2.0-preview.2` tag is created once and never moved.
6. Tag smoke and a clean public archive verification pass before publishing the
   GitHub prerelease.

## Unchanged hosted boundary

The hosted free-trial gate remains `NO_GO`, all eleven production prerequisites
remain `UNRESOLVED`, and the deterministic public Demo remains the active
Strategy A surface. This candidate does not authorize accounts, real-data
uploads, hosted model processing, server-side persistence, or hosted export.
