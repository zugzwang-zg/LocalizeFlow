# Release, smoke-test, and rollback runbook

Last updated: 2026-08-16

## Release authority

The current repository may prepare local release evidence but must not deploy
or open a hosted trial without explicit owner approval and all D-stage gates.
The Hosted Trial legal checklist, provider disclosure, production monitoring,
external alert delivery, support coverage, backup/restore, and deletion drill
must match the actual environment.

## Pre-release gate

1. Freeze the commit, dependency lockfiles, prompt/schema/rule versions, model
   route, quota values, operational thresholds, and three emergency switches.
2. Confirm no secret, personal/customer data, raw production logs, or private
   incident material is in the change or artifact.
3. Run:

```powershell
.\.venv\Scripts\uv.exe sync --locked --extra dev
.\.venv\Scripts\uv.exe run ruff check .
.\.venv\Scripts\uv.exe run mypy
.\.venv\Scripts\uv.exe run pytest -q
.\.venv\Scripts\uv.exe run python prompts\tests\validate_prompts_offline.py
.\.venv\Scripts\uv.exe run python app\main.py --smoke-test
.\.venv\Scripts\uv.exe run python scripts\run_operations_drill.py
```

Then run in `web/`:

```powershell
pnpm install --frozen-lockfile
pnpm security:audit
pnpm lint
pnpm test
pnpm build
```

4. Verify cross-tenant denial, quota/cost reservation, model and export kill
   switches, hard-gate export denial, deletion, and a synthetic end-to-end run.
5. Record command results, commit, reviewer, timestamp, known exceptions, and
   rollback target. CI success alone is not proof of a production smoke test.

## Deployment smoke

Use fictional data only:

1. Verify public page and independent health probe.
2. Verify sign-in/session/tenant boundaries in the deployed environment.
3. Confirm monitoring receives a content-free health event and alert delivery
   works outside the service.
4. With exports still closed, enable the smallest model quota and run one
   synthetic task; verify provider route, Schema, facts, packaging, latency,
   tokens, cost, audit metadata, and no raw body logging.
5. Verify a blocked output cannot export, then verify one reviewed safe output.
6. Re-disable model calls unless the release approval explicitly opens them.

## Rollback

1. Declare the incident and disable model calls/exports as appropriate.
2. Select the last immutable deployment artifact whose smoke evidence passed;
   do not move an existing Git tag or use `git reset --hard` as an operational
   rollback mechanism.
3. Use the hosting platform's version rollback, or create a reviewed revert
   commit when code must be reversed.
4. Treat database/storage changes separately: use a tested backward-compatible
   migration or restore plan; never delete production data to make old code run.
5. Repeat deployment smoke and verify recovery alerts/status.
6. Record the failed and restored versions, data migration state, switch state,
   residual risk, and follow-up owner.

The current project has no hosting platform or immutable deployment artifact
configured, so the production rollback step remains untested and blocks hosted
trial launch.
