# Open-source release candidate readiness

> Candidate: `v0.2.0-preview.1`
> Audit date: 2026-08-16
> Local status: preparing Draft PR
> Formal release: not authorized before owner acceptance and protected checks

## Recommendation

Use `v0.2.0-preview.1`, not a stable `v0.2.0` release. The candidate contains a
substantial product, evidence, security, privacy, and operations increment over
`v0.1.0-preview.1`, but it still has a small synthetic evaluation, AI-assisted
review, no real-user adoption evidence, and a hosted free-trial `NO-GO`.

## GitHub repository audit

- Repository visibility: public.
- Default branch: `main`.
- License recognized by GitHub: Apache-2.0.
- Public Demo is configured as the repository homepage.
- Issues enabled; Wiki and Discussions intentionally disabled.
- Dependabot security updates, secret scanning, push protection, and private
  vulnerability reporting are enabled.
- `main` requires a pull request, six current CI/CodeQL checks, an up-to-date
  branch, linear history, conversation resolution, and blocks force pushes and
  deletion.
- Required project labels are present or created as part of this candidate.
- Existing public prerelease: `v0.1.0-preview.1`.

## Candidate contents

- Recruiter-first README and public Web portfolio experience.
- 30-pair frozen evaluation with explicit limitations and provenance.
- Structured packaging facts and fail-closed fact/rule/export gates.
- Local Closed Beta reference controls for safe import, tenant separation,
  quota/cost limits, model gateway validation, audit, deletion, and operations.
- Public legal/trust documents and blocked hosted-policy templates.
- Machine-readable `NO_GO` and `UNRESOLVED` release decisions.
- Apache-2.0 notices and explicit AI-generated material disclosures.

## Current release gate

The local candidate may be pushed to a Draft PR when
`scripts/check_open_source_release_candidate.py --expect-draft-ready`, the full
Python/Web regression, dependency audits, prompt validation, startup smoke,
operations drill, and fail-closed checks pass.

The formal prerelease remains blocked until:

1. The project owner accepts this stage and confirms the version/tag.
2. The Draft PR targets `main` and all protected CI/CodeQL checks pass.
3. `CHANGELOG.md` replaces `TBD` with the actual release date.
4. The exact candidate runs through the manually dispatched `Release smoke`.
5. The PR is merged without bypassing branch protection.
6. The public source archive is re-downloaded and smoke-tested before the
   GitHub prerelease is published.

## Local verification results

| Gate | Result |
|---|---|
| Candidate decision | `DRAFT_READY`; formal release authorization remains false |
| Python tests | 141 passed plus 6 subtests |
| Python coverage | 72.22%, above the 70% threshold |
| Ruff / mypy | Passed; 14 typed source files reported no issues |
| Startup smoke | Passed |
| Prompt/schema validation | 6 schemas, 9 prompts, 0 API calls; passed |
| Operations drill | Passed; incident recovered to healthy, no content bodies logged |
| Hosted free-trial gate | Expected `NO_GO`; 0 validation errors and 0 model calls |
| Hosted prerequisites | Expected `UNRESOLVED`; 11 unresolved decisions |
| Web | 9 tests, lint, production build, and complete dependency audit passed |
| Python dependency audit | No known vulnerabilities |
| Official platform sources | 7/7 Google and TikTok URLs reachable on 2026-08-16 |
| Candidate credential/size scan | 244 candidate files, 0 credential-pattern hits, 0 files over 95 MB |
| Git diff whitespace | Passed |

The first Web command attempt found a stale local `pnpm` cache shim. The same
pinned pnpm 11.19.0 tool was restored through Corepack; frozen-lockfile install,
supply-chain policy verification, audit, lint, tests, and both builds then
passed without changing dependency versions.

## Hosted-trial separation

This open-source candidate does not authorize accounts, real-data uploads,
hosted model processing, server-side project persistence, or hosted content
export. The deterministic public Demo remains the active Strategy A surface.
