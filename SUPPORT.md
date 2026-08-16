# LocalizeFlow support policy

Last updated: 2026-08-16

## Current support scope

The public preview is a portfolio and open-source reference project, supported
on a best-effort basis. It does not offer 24/7 support, guaranteed response
times, or a hosted service-level agreement.

Use the GitHub **Support request** form for installation, deterministic Demo,
documentation, or workflow questions. Use the **Bug report** form for a
reproducible defect. Search existing issues first and include a version or
commit, affected surface, expected behavior, actual behavior, and sanitized
reproduction steps.

Never submit secrets, personal data, customer content, private product facts,
production credentials, or security exploit details in a public issue.
Security reports follow `SECURITY.md`.

## Incident classification and internal response objectives

These are maintainer operating objectives for a scheduled Beta window, not a
public SLA. The clock begins when a monitored alert or complete report reaches
the designated maintainer during the published support window. A hosted launch
must publish actual coverage and test alert delivery first.

| Level | Examples | Acknowledge target | Containment/update target |
|---|---|---:|---:|
| P0 critical | Cross-tenant access, secret/personal-data leak, fact-gate bypass, uncontrolled model cost, undisclosed provider route change, deletion failure, complete hosted outage | 30 minutes | Start containment within 1 hour; public update every 60 minutes when appropriate |
| P1 major | Elevated generation/schema failure, severe latency, export failure, partial outage, repeated incorrect blocking with no safety bypass | 4 business hours | Mitigation plan within 1 business day; update each business day |
| P2 standard | Isolated defect, localization quality issue, documentation, usability, feature request | 2 business days | Triage decision within 5 business days |

Privacy or legal notification deadlines are handled according to applicable
requirements and are not extended by these internal targets.

## Ticket workflow

1. `new`: validate scope and remove/redact sensitive material where permitted.
2. `triaged`: assign P0/P1/P2, owner, affected version, and next update time.
3. `investigating`: reproduce with fictional or sanitized data and record
   evidence without copying user content.
4. `mitigating`: use the model/export kill switches or rollback runbook as
   required; preserve necessary evidence securely.
5. `monitoring`: verify recovery against smoke tests and operational metrics.
6. `resolved` or `declined`: record the outcome, release/fix reference, and a
   content-free explanation.

See `docs/operations/INCIDENT_RESPONSE.md` for P0/P1 handling and
`docs/operations/RELEASE_RUNBOOK.md` for rollback and verification.
