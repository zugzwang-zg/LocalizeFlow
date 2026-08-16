# Hosted trial implementation batches

This backlog starts only after the owner records the relevant D5 selections.
Do not start a later batch to compensate for an unresolved earlier dependency.

## Batch 0 — scope and authority

1. Choose Strategy A, B, or C in the decision register.
2. Record the operator, jurisdictions, budget ceiling, supported cohort, trial
   duration, excluded data and supported workflow.
3. Establish private privacy/support/security contacts and primary/backup
   ownership.
4. Verify relay and model-provider data terms before any user-data model call.

Acceptance evidence: selected entries in the prerequisite register, private
source records, sanitized public evidence references, and model/export switches
still closed.

## Batch 1 — immutable hosting foundation

1. Create separate development and production projects/accounts.
2. Configure the chosen region, TLS, trusted proxies, secret manager/KMS and an
   immutable deployment identifier.
3. Add infrastructure configuration without committing credentials.
4. Deploy a fictional-data health candidate with accounts, uploads, model calls
   and exports disabled.
5. Record the candidate URL privately and the immutable version publicly where
   safe.

Acceptance evidence: architecture and data-flow diagrams, configuration export,
TLS/proxy test, secret scan, deployment identifier and fictional-data smoke log.

## Batch 2 — identity, tenant data and deletion

1. Implement invite-only identity verification, recovery, session expiry,
   revocation and administrative access.
2. Enforce tenant authorization server-side for every read, write, model run,
   export and delete operation.
3. Replace local SQLite with the selected durable encrypted stores and KMS.
4. Inventory database, uploads, cache, logs, support records and backups.
5. Exercise cross-tenant denial, project/account export, active-store deletion,
   backup restoration and backup purge with fictional data.

Acceptance evidence: denial matrix, configuration record, export manifest,
deletion receipt, restore/purge timing and body-free audit events.

## Batch 3 — quota, model route and cost containment

1. Replace process-local counters with atomic multi-instance reservations.
2. Bind account/project/client limits to trusted identity and edge signals.
3. Connect the verified relay/model route using data minimization and
   no-training settings.
4. Reconcile estimated and provider-billed cost; fail closed on missing price,
   counter failure or budget exhaustion.
5. Exercise concurrency, retry/idempotency, bypass, global cap, administrative
   suspension and external abuse alerting with fictional inputs.

Acceptance evidence: concurrency results, redacted provider settings, billing
reconciliation, cap/suspension drill and zero raw-body logs.

## Batch 4 — monitoring, response and rollback

1. Connect durable metrics and an independent service-external probe.
2. Deliver P0/P1 alerts outside the application to primary and backup owners.
3. Connect the status surface without publishing sensitive incident detail.
4. Exercise model/export containment, credential rotation, immutable rollback,
   database compatibility and recovery notification.
5. Run GitHub Release smoke and deployment smoke against the exact candidate.

Acceptance evidence: alert delivery/acknowledgement times, probe history,
release-smoke URL, failed/restored versions, migration state and recovery log.

## Batch 5 — controlled participant evidence

1. Keep the public GitHub form as interest registration only; never request
   product files, personal contact details or confidential content there.
2. Screen and approve participants through the designated private channel.
3. Complete agreements, provider disclosures, data authority and technical
   preflight before access.
4. Run the defined real-user Beta with at least two independent target-language
   reviews, separate en-US/es-MX reporting, withdrawal and deletion rehearsal.
5. Record adoption evidence honestly; AI review remains supplementary evidence.

Acceptance evidence: private approval records, content-free participant IDs,
completed task/reviewer sheets, withdrawal/deletion receipt and adoption report.

## Batch 6 — final release candidate

1. Freeze code, infrastructure, legal documents, providers, regions, prices,
   quotas, contacts, runbooks and evidence.
2. Mark a prerequisite `verified` only when every required artifact has been
   reviewed; record explicit owner approval last.
3. Run the prerequisite checker with `--require-verified` and the free-trial
   checker with `--require-go`.
4. Open only a narrowly capped invite cohort, observe it, and retain the ability
   to disable model calls and content exports immediately.

Acceptance evidence: both machine gates pass, exact artifact/drill record,
effective policy versions, signed release decision and rollback target.
