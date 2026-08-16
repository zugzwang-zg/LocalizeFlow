# Incident response runbook

Status: local tabletop process; external delivery/on-call not connected

Last updated: 2026-08-16

## Roles

For the current solo-maintainer project, one person may hold several roles but
must explicitly record them:

- Incident commander: severity, containment, decision log, and next update.
- Technical lead: diagnosis, rollback, switch changes, and verification.
- Communications lead: status/support updates without sensitive data.
- Privacy/security lead: evidence handling, notification assessment, and
  private coordination.

A hosted trial must name a primary and backup contact before launch.

## Declare and classify

1. Create a private incident record from `INCIDENT_TEMPLATE.md`; use a public
   issue only for sanitized status communication.
2. Record UTC and local start time, detector, affected surface/version, known
   symptoms, current data exposure assessment, incident commander, and next
   update time.
3. Classify P0/P1/P2 using `SUPPORT.md`. Any cross-tenant read, leak, gate
   bypass, runaway cost, undisclosed provider-route change, or deletion failure
   is P0 even if only one request is known.
4. Do not copy prompts, uploads, outputs, tokens, credentials, personal data, or
   raw account/SKU identifiers into metrics, tickets, or public updates.

## Contain

For P0, take the smallest safe containment actions immediately:

1. Set `LOCALIZEFLOW_OPS_MODEL_CALLS_ENABLED=false` for provider, cost, data
   route, schema, or generation-safety incidents.
2. Set `LOCALIZEFLOW_OPS_EXPORTS_ENABLED=false` for gate bypass, cross-tenant,
   unauthorized-output, or audit-integrity incidents.
3. If availability or a release caused the incident, roll back to the last
   verified deployment using `RELEASE_RUNBOOK.md`.
4. Revoke/rotate affected credentials through the provider's secret manager;
   never put replacement values in Git, chat, or the incident record.
5. Preserve only necessary, access-controlled evidence. Do not access data that
   is not needed to confirm impact.
6. Keep user privacy export/deletion available unless the incident commander
   documents why that would worsen the incident and provides a safe alternative.

## Communicate

- P0: acknowledge within the target window and update every 60 minutes while
  user impact continues, when a public update is appropriate.
- P1: update each business day until mitigated.
- State observed impact, affected surface/time, current containment, safe user
  action, and next update time. Separate confirmed facts from hypotheses.
- Do not name a provider or claim a breach/root cause until verified.
- Security and privacy details remain in private channels; public status should
  link to `STATUS.md` or a pinned sanitized incident issue.

## Recover

1. Fix or roll back the cause and obtain review proportional to severity.
2. Run startup smoke, critical workflow regression, tenant isolation, quota,
   operations, prompt, Web test/build, and dependency/security gates.
3. Use fictional data for the first recovery check; do not use customer data as
   a probe.
4. Confirm metrics/alerts recover and no new P0 safety event appears.
5. Re-enable exports before model calls only when export authorization and
   safety gates are verified. Re-enable model calls last, with the smallest
   quota and a synthetic request.
6. Record the exact deployment/commit, approver, switch state, evidence, and
   recovery time.

## Close and learn

Within five business days of a P0/P1 resolution, complete a blameless review:
timeline, impact, detection gap, contributing conditions, what worked, what did
not, corrective actions with owner/due date, and proof that no private content
was copied into the review. Update tests/runbooks before marking preventative
actions complete.
