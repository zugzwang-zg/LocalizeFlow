# Portfolio strategy decision — Strategy A

Decision date: 2026-08-16

Decision owner: project owner

Status: **Selected for the current portfolio phase**

## Decision

LocalizeFlow will continue with **Strategy A: portfolio-only public Demo**.
The project will maintain its open-source repository, frozen fictional-data Web
Demo, local deterministic/Closed Beta reference implementation, evaluation
evidence, and explicit production-readiness gaps. It will not spend time or
money on a hosted account system or accept real product data in the current
phase.

This is a scope decision, not abandonment of the product. Strategy B or C can
be reconsidered when a concrete opportunity makes the additional evidence more
valuable than the cost and operating responsibility.

## Weighted score

Scores use 1 (poor) to 5 (strong) for the project's current portfolio goal.

| Criterion | Weight | A: portfolio Demo | B: synthetic hosted rehearsal | C: real-data Beta/trial |
|---|---:|---:|---:|---:|
| Portfolio value per effort | 30% | 4 | 5 | 5 |
| Time to credible evidence | 25% | 5 | 2 | 1 |
| Fit with current cash constraint | 20% | 5 | 3 | 1 |
| Privacy/legal/security risk fit | 15% | 5 | 4 | 1 |
| Solo operational feasibility | 10% | 5 | 2 | 1 |
| **Weighted score** | **100%** | **4.70** | **3.40** | **2.00** |

Strategy B can demonstrate infrastructure work, but it duplicates evidence
already represented by the D1–D5 controls without proving real adoption.
Strategy C has the highest theoretical product evidence, but it is not credible
without actual participants, independent reviewers, operator/provider terms,
durable tenant and deletion controls, alerting, rollback, support and budget.

## Current external constraints

Official provider documentation was reviewed on 2026-08-16:

- [Render Free](https://render.com/docs/free) says free services are for
  preview/hobby use rather than production; free web services sleep after 15
  minutes, have an ephemeral filesystem, cannot attach persistent disks, and
  free Postgres expires after 30 days without backups.
- [Supabase project pausing](https://supabase.com/docs/guides/platform/free-project-pausing)
  documents inactivity pausing for Free Plan projects.
- [Supabase backups](https://supabase.com/docs/guides/platform/backups) recommends
  that free-tier projects create and maintain their own off-site backups.
- [Streamlit Community Cloud sharing](https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app)
  can share public or limited private apps, but sharing is not a substitute for
  the application's own tenant, data lifecycle, provider disclosure and support
  controls.

These services remain useful candidates for a future fictional-data rehearsal.
Their free tiers do not, by themselves, make a real-data free trial production
ready.

## Current scope

### Continue

- Public deterministic Demo using only frozen fictional data.
- Local setup, tests, CI, security maintenance and reproducible evidence.
- Portfolio case study, architecture explanation, failure cases and honest
  limitations.
- Interest-only Beta registration that accepts no personal or product data.
- Optional local model tests with owner-controlled synthetic inputs and strict
  cost limits; results must remain labeled as AI/synthetic evidence.

### Do not start

- Public registration or hosted identity.
- Real product/customer uploads or persistence.
- Hosted user-data model calls or content export.
- Paid hosting, database, monitoring or support commitments.
- Claims of real-user adoption, professional review, uptime, SLA or production
  readiness.

## Reassessment triggers

Evaluate Strategy B or C only when at least one value trigger and every matching
safety/resource trigger are present:

1. A concrete prospective user, accelerator or partner requests hosted
   infrastructure evidence that the current repository cannot demonstrate.
2. A dedicated monthly budget and primary/backup operational owner exist.
3. Authorized participants and two independent en-US/es-MX reviewers exist.
4. Operator, jurisdictions, private contacts and relay/model data terms can be
   truthfully completed.
5. There is time to finish and rehearse hosted identity, tenant, quota, backup,
   deletion, monitoring, alert and rollback controls.

Until then, Strategy A is an intentional product decision, and D5 remains
`UNRESOLVED` for hosted production prerequisites.
