# Maintainer release checklist

Use this checklist for `v0.1.0-preview.1`. Repository settings and publishing
steps intentionally occur only after the release candidate has been reviewed.

## 1. Review and merge the release candidate

- [ ] Review the complete diff, especially license ownership, synthetic-content
      disclosures, dependency overrides, and security contact instructions.
- [ ] Confirm the collective `LocalizeFlow contributors` copyright wording,
      or replace it with the project's legal copyright holder before release.
- [ ] Push the release candidate to a branch and open a pull request.
- [ ] Wait for CI and CodeQL to pass on GitHub-hosted runners.
- [ ] Confirm the README badges resolve after the workflows run.

## 2. Configure repository security

In GitHub, open **Settings → Code security and analysis**:

- [ ] Enable Dependency graph and Dependabot alerts.
- [ ] Enable Dependabot security updates.
- [ ] Enable secret scanning and push protection where available.
- [ ] Enable Private vulnerability reporting.
- [ ] Verify `SECURITY.md` appears under the repository Security tab.

## 3. Create labels

Create these labels before accepting external issues:

- [ ] `needs-triage`
- [ ] `fact-safety`
- [ ] `platform-rule`
- [ ] `localization`
- [ ] `accessibility`
- [ ] `dependencies`
- [ ] `python`
- [ ] `web`
- [ ] `epic:open-source`
- [ ] `epic:fact-safety`
- [ ] `epic:demo`
- [ ] `epic:beta`
- [ ] `epic:free-trial`
- [ ] `epic:security`
- [ ] `epic:privacy`

## 4. Protect `main`

After the first pull request has produced check names, configure a ruleset for
`main`:

- [ ] Require a pull request before merging.
- [ ] Require the Python 3.11, 3.12, 3.13 and Web CI checks.
- [ ] Require both CodeQL language checks.
- [ ] Require branches to be up to date before merge.
- [ ] Block force pushes and branch deletion.
- [ ] Keep maintainer bypass limited and documented.

## 5. Run the final local gate

```powershell
.\.venv\Scripts\uv.exe sync --locked --extra dev
.\.venv\Scripts\uv.exe run ruff check .
.\.venv\Scripts\uv.exe run mypy
.\.venv\Scripts\uv.exe run pytest -q --cov=src --cov=app --cov-fail-under=70
.\.venv\Scripts\uv.exe run python prompts\tests\validate_prompts_offline.py
.\.venv\Scripts\uv.exe run python app\main.py --smoke-test
cd web
pnpm install --frozen-lockfile
pnpm lint
pnpm test
pnpm build
pnpm security:audit
```

- [ ] Run a Python dependency audit against the installed clean environment.
- [ ] Confirm no secrets exist in the worktree or Git history.
- [ ] Confirm PDF, PPTX, video, screenshots, and office files contain no private
      comments, paths, credentials, customer data, or unwanted author metadata.
- [ ] Confirm all official platform-rule URLs and verification dates.

## 6. Publish the preview

- [ ] Replace `TBD` in `CHANGELOG.md` with the release date.
- [ ] Merge only after all required checks pass.
- [ ] Create annotated tag `v0.1.0-preview.1` from the reviewed `main` commit.
- [ ] Create a GitHub prerelease using `RELEASE_NOTES.md`.
- [ ] Attach only reviewed release assets; source archives are sufficient unless
      an additional artifact has a documented need.
- [ ] Re-download the source archive into a clean directory and repeat the
      startup smoke test.
- [ ] Verify GitHub recognizes Apache-2.0 and displays the Security policy.
- [ ] Record the release URL and final commit in
      `reports/open_source_readiness.md`.

## Rollback

If a critical license, secret, personal-data, or dependency issue appears,
mark the release unavailable, rotate any affected credential, publish a clear
security notice through the private-reporting process, and issue a corrected
preview from a new tag. Do not silently move an existing public tag.
