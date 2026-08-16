# Hosted trial prerequisite decisions

Status: **UNRESOLVED — portfolio-only public Demo remains the active strategy.**

This register turns the five blocked hosted-release gates into owner decisions.
It is not a vendor selection, deployment approval, legal opinion, or invitation
to upload real product data. The machine-readable source is
`reports/hosted_trial_prerequisites.json`.

## Strategy decision

| Strategy | Scope | Cost and risk | Current decision |
|---|---|---|---|
| A. Portfolio-only public Demo | Frozen fictional data; no accounts or model API | Lowest cost; preserves the verified portfolio story | **Active** |
| B. Synthetic infrastructure rehearsal | Invite-only infrastructure tests using fictional data | Hosting effort and possible provider cost; still not real-user evidence | Optional after stack selection |
| C. Real-data Closed Beta / free trial | Authorized uploads, model route, isolated accounts, export and deletion | Requires every D5 prerequisite, provider evidence, operations coverage and appropriate review | Blocked |

Given the project's portfolio purpose and current time/economic constraints,
Strategy A is the recommended default. Strategy B is useful only when its cost
buys evidence needed for a concrete application or interview. Strategy C must
not be started merely to remove a checklist item.

## Owner decision worksheet

Record selections in the JSON register only after the owner has chosen them.
Change a prerequisite to `selected` when a concrete option is chosen, and to
`verified` only after every listed evidence item exists and has been reviewed.

| Decision | Minimum owner input | Safe default while open |
|---|---|---|
| Operator and jurisdictions | Responsible person/entity, address, countries, applicable law, age/eligibility | No accounts or active hosted terms |
| Private contacts | Privacy, support, security escalation, legal notice; primary and backup owner | No hosted request channel claimed |
| Runtime and region | Runtime, domain/TLS, network boundary, region, immutable deployment method | Deterministic public Demo only |
| Identity and tenant boundary | Managed identity, invite allowlist, recovery, session, MFA/admin, server authorization | Registration disabled |
| Data, backup and KMS | Database, optional object storage/cache, encryption, backup, restore and purge | No hosted persistence of real content |
| Relay and model terms | Both legal entities, terms/DPA, regions, retention, training, human access, subprocessors, deletion | User-data model calls disabled |
| Quota, billing and abuse | Durable atomic store, trusted client identity, total budget, reconciliation, suspension and alerting | Owner-funded calls closed |
| Monitoring and on-call | External probe, durable metrics, off-service alerts, status channel, primary/backup coverage | No uptime or SLA claim |
| Deployment and rollback | Release promotion, migrations, immutable rollback, credential rotation and notification | No deployment from local evidence |
| Participants and reviewers | Authorized participants, two independent target-language reviewers, schedule and withdrawal | Interest registration only |
| Final approval | Exact commit/artifact, residual risk, effective policies, budget and opening cap | NO-GO |

Local `.env` values, screenshots containing secrets, private agreements,
participant identities and raw provider invoices must never be committed. Keep
private source evidence outside the repository and add only a sanitized evidence
record or stable reference suitable for public review.

## Machine check

Current safe state:

```powershell
.\.venv\Scripts\uv.exe run python scripts\check_hosted_trial_prerequisites.py --expect-unresolved
```

After every prerequisite is verified and explicit owner approval is recorded:

```powershell
.\.venv\Scripts\uv.exe run python scripts\check_hosted_trial_prerequisites.py --require-verified
```

`--require-verified` is necessary but not sufficient for release. The separate
free-trial gate must also return GO, the exact hosted candidate must pass its
drills, and the owner must approve opening it.
