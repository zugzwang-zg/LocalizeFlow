# Maintainer release checklist

> Candidate: `v0.2.0-preview.1`
> Candidate state: Draft PR preparation
> Formal release: blocked until owner acceptance, required GitHub checks, and
> the clean-source smoke test pass

This checklist applies to the Apache-2.0 source preview and deterministic
public Demo. It does not authorize a hosted free trial or real-data processing.

## 1. Repository controls

- [x] Repository is public and GitHub recognizes Apache-2.0.
- [x] Issues are enabled; Wiki and Discussions remain intentionally disabled.
- [x] Dependency graph/Dependabot security updates are enabled.
- [x] Secret scanning and push protection are enabled.
- [x] Private vulnerability reporting is enabled.
- [x] `SECURITY.md` is present.
- [x] `main` requires a pull request, current CI/CodeQL checks, an up-to-date
      branch, linear history, conversation resolution, and blocks force pushes
      and deletion.
- [x] Maintainer labels include triage, safety, localization, accessibility,
      dependency, Python, Web, epic, incident, and support scopes.

## 2. Review the candidate

- [ ] Review the complete Draft PR diff, especially license ownership,
      synthetic-content disclosures, generated-image provenance, security
      contacts, release boundaries, and the 30-case evaluation claims.
- [ ] Confirm `LocalizeFlow contributors` is the intended copyright wording,
      or replace it with the legal copyright holder before release.
- [ ] Confirm the public Demo URL, README anchors, trust pages, and release-note
      links resolve from the GitHub-rendered branch.
- [ ] Confirm `v0.2.0-preview.1` is the desired tag and replace `TBD` in
      `CHANGELOG.md` with the actual release date.
- [ ] Resolve or explicitly defer open dependency PRs; do not merge unreviewed
      upgrades into the frozen candidate.

## 3. Required local gate

```powershell
.\.venv\Scripts\uv.exe sync --locked --extra dev
.\.venv\Scripts\uv.exe run ruff check .
.\.venv\Scripts\uv.exe run mypy
.\.venv\Scripts\uv.exe run pytest -q --cov=src --cov=app --cov-fail-under=70
.\.venv\Scripts\uv.exe run python prompts\tests\validate_prompts_offline.py
.\.venv\Scripts\uv.exe run python app\main.py --smoke-test
.\.venv\Scripts\uv.exe run python scripts\run_operations_drill.py
.\.venv\Scripts\uv.exe run python scripts\check_open_source_release_candidate.py --expect-draft-ready
.\.venv\Scripts\uv.exe run python scripts\check_hosted_trial_prerequisites.py --expect-unresolved
.\.venv\Scripts\uv.exe run python scripts\check_free_trial_release_gate.py --expect-no-go
cd web
pnpm install --frozen-lockfile
pnpm security:audit
pnpm lint
pnpm test
pnpm build
```

- [x] Run the complete local gate against the candidate tree; repeat only if
      the candidate changes after the final commit.
- [x] Confirm no secrets, personal/customer data, raw production logs, or
      private incident material exists in the candidate or Git history.
- [x] Confirm PDF, PPTX, video, screenshots, workbooks, and generated images
      have the documented provenance and no unwanted private metadata.
- [x] Run Python and Web dependency audits with no known vulnerabilities.
- [x] Confirm all seven official platform-rule links remain reachable; keep the
      frozen 2026-07-28 rule verification date for evaluation reproducibility.

## 4. GitHub candidate gate

- [ ] Draft PR targets `main` from the candidate branch.
- [ ] Python 3.11, 3.12, 3.13 and Web CI pass on the exact head SHA.
- [ ] CodeQL Python and JavaScript/TypeScript analyses pass.
- [ ] README badges resolve on the branch.
- [ ] Run the `Release smoke` workflow on the exact candidate SHA and record
      its URL in `reports/open_source_release_candidate.md`.
- [ ] All review conversations are resolved and the branch is up to date.

## 5. Publish only after owner acceptance

- [ ] Merge the reviewed PR without bypassing branch protection.
- [ ] Confirm the merge commit/tree matches the reviewed candidate.
- [ ] Create annotated tag `v0.2.0-preview.1` from reviewed `main`; never move
      an existing tag.
- [ ] Create a GitHub prerelease using `RELEASE_NOTES.md`.
- [ ] Attach only reviewed assets; source archives are sufficient by default.
- [ ] Re-download the public source archive into a clean directory and repeat
      startup and release-candidate smoke checks.
- [ ] Record the release URL, final commit, CI, CodeQL, release-smoke, and
      clean-source evidence in `reports/open_source_release_candidate.md`.

## Rollback

If a critical license, secret, personal-data, dependency, or evidence issue is
found, do not publish or merge. If discovered after release, mark the affected
release unavailable, rotate credentials when applicable, publish a security
notice through the private-reporting process, and issue a corrected prerelease
from a new tag. Never silently move a public tag.
