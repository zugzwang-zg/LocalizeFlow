# Hosted free-trial readiness decision

Audit date: 2026-08-16

Decision: **NO-GO — keep registration, user uploads, user-data model calls, and
hosted content export closed.**

This report closes the repository-level D1–D4 implementation cycle. It does
not authorize deployment and does not claim legal, security, privacy, or
production approval.

## Gate matrix

| Stage D release gate | Local evidence | Hosted release status | Decision reason |
|---|---|---|---|
| Real-user data policy is effective | Partial: scoped public-preview documents, no-training product rule, blocked hosted drafts | Blocked | Operator, privacy contact, actual providers/regions/transfers/retention, production inventory, and appropriate approval are unresolved |
| Account, tenant, and permission tests pass | Passed locally: encrypted SQLite, tenant-filtered read/write/export/delete, session expiry | Blocked | No hosted identity/allowlist, HTTPS/secure cookies, KMS, recovery/MFA, or multi-instance authorization evidence |
| Quota, rate, and cost limits are verified | Passed locally: account/project/client limits and conservative reservations | Blocked | Process-local counters; no trusted edge identity, durable atomic storage, billing reconciliation, admin control, or external abuse delivery |
| Critical facts and packaging contradictions cannot cross export | Passed in deterministic and Closed Beta quality tests | **Ready at repository level** | Hard failures block export and human review cannot override a critical failure |
| Production monitoring, alerts, rollback, and support are rehearsed | Local synthetic drill passed | Blocked | No durable metrics, external probes/alerts, actual platform rollback, on-call delivery, or hosted release-smoke record |
| Users can export/delete projects and accounts | Passed against local primary store | Blocked | No production stores, caches, logs, support systems, backups, identity-verification, or privacy-request rehearsal |

Machine-readable evidence is in `reports/free_trial_gate.json`. Run:

```powershell
.\.venv\Scripts\uv.exe run python scripts\check_free_trial_release_gate.py --expect-no-go
```

An actual hosted free-trial candidate must change the command to
`--require-go`. That command must fail while any release status is `blocked`,
any evidence path is missing, the declared decision differs from the computed
decision, or the fail-closed public/configuration boundaries are absent.

The owner decisions that precede implementation are tracked separately in
`reports/hosted_trial_prerequisites.json`. The current strategy and dependency-
ordered batches are documented in
`docs/operations/HOSTED_TRIAL_DECISION_REGISTER.md` and
`docs/operations/HOSTED_TRIAL_IMPLEMENTATION_BACKLOG.md`. Validate the current
safe state with:

```powershell
.\.venv\Scripts\uv.exe run python scripts\check_hosted_trial_prerequisites.py --expect-unresolved
```

## What is genuinely complete

- D1: locally testable quota, rate, idempotency, and cost-reservation primitive.
- D2: locally encrypted account/project store with tenant filters, export,
  deletion, session expiry, and body-free audit events.
- D3: public-preview privacy/terms/AUP/disclaimer, no-training rule, and blocked
  hosted legal/provider templates.
- D4: privacy-safe operational metric contract, deterministic alerts, model and
  content-export switches, support/incident/runbook documents, and a synthetic
  alert/containment/recovery drill.
- Fact and packaging gates: repository-level release requirement passes.

## Minimum work before reassessment

1. Select the actual operator, hosting/identity/database/storage/backup stack,
   regions, support/privacy contacts, relay, and model provider.
2. Complete legal/provider records from contracts, DPA, account settings, and
   production evidence; remove every `[REQUIRED]` marker only after review.
3. Replace local sessions, counters, storage, and metrics with trusted,
   durable, atomic, multi-instance controls; connect HTTPS, KMS, backups, and
   trusted edge identity.
4. Connect independent probes and external P0/P1 delivery; run tenant,
   cost/abuse, deletion/backup, credential-rotation, rollback, and incident
   exercises in the exact hosted candidate.
5. Run the GitHub Release smoke workflow and production smoke on the immutable
   candidate, then attach URLs and redacted evidence to the gate record.
6. Conduct the planned real-user Closed Beta. AI reviews are useful product
   evidence but do not establish real-user adoption, usability, or independent
   professional approval.

Only then rerun the gate, obtain the required approvals, and make a separate
owner decision about opening a narrowly capped trial.
