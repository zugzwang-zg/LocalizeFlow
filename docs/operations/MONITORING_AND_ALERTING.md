# Monitoring and alerting specification

Status: local reference implementation; hosted monitoring not connected

Last updated: 2026-08-16

## Objectives

Detect availability, quality, cost, safety, and workflow failures without
placing uploaded content, generated text, credentials, email addresses, raw
account IDs, or raw SKU IDs in operational events.

`src/operations.py` keeps a bounded process-local event window for tests and a
single-process portfolio demonstration. Account and SKU identifiers are stored
only as HMAC-SHA256 digests. Events use bounded machine error codes rather than
exception messages or response bodies. The default retention target is seven
days and 5,000 events, whichever limit is reached first.

This store resets on restart and cannot aggregate multiple instances. It is not
the source for a production SLA, privacy request, billing reconciliation, or
forensic record.

## Metric contract

| Metric | Numerator / denominator | Default alert |
|---|---|---|
| Availability | Successful independent health checks / all health checks | P1 below 99%; P0 below 95% |
| Generation request success | Successful application requests, including safe cache hits / all generation requests | P1 below 95%; P0 below 80% |
| Page error rate | Failed page requests / all page requests | P1 above 5%; P0 above 15% |
| Generation p95 latency | 95th percentile of non-cache provider runs | P1 above 30 s; P0 above 60 s |
| Model timeout rate | Timed-out non-cache provider runs / non-cache provider runs | Dashboard; investigate with success/latency |
| Retry rate | Non-cache provider runs with more than one attempt / non-cache provider runs | P1 above 10%; P0 above 25% |
| Schema success | Provider runs with valid JSON/Schema / runs with a known schema outcome | P1 below 98%; P0 below 90% |
| Cost by account/SKU | Sum of metered or conservatively reserved cost grouped by HMAC identifier | D1 budget limits remain the hard control |
| Fact hard blocks | Sum of failed deterministic quality checks | Trend and false-positive review; a bypass is P0 |
| False-positive feedback | Explicit feedback items categorized as an incorrect block | Weekly quality review |
| Export completion | Successful hosted content downloads / attempted hosted content downloads | P1 below 95%; P0 below 80% |
| User feedback | Count of content-free feedback events | Weekly support review |

Rate alerts require five samples by default. The minimum protects a portfolio
demo from meaningless one-request percentages; production thresholds and
minimum traffic must be calibrated from a documented baseline. Safety events
do not wait for a sample threshold.

## Immediate P0 safety events

- cross-tenant access;
- secret or personal-data exposure;
- a critical fact contradiction crossing the export gate;
- uncontrolled model cost;
- undisclosed relay/model data-route change;
- project/account deletion failure.

Each creates a P0 alert and invokes the containment steps in
`INCIDENT_RESPONSE.md`.

## Emergency controls

The Closed Beta path requires three independent environment controls:

```text
LOCALIZEFLOW_OPS_MONITORING_ENABLED=true
LOCALIZEFLOW_OPS_MODEL_CALLS_ENABLED=true
LOCALIZEFLOW_OPS_EXPORTS_ENABLED=true
```

All default to `false`. Monitoring must be valid before model calls or hosted
content exports can open. Turning off model calls prevents new provider calls;
turning off exports prevents the reviewed model-content audit download. It does
not disable privacy access/export or deletion controls, which must remain
available unless preserving them would worsen an active security incident.

Changing a switch in a hosted environment requires a controlled configuration
change and restart/redeploy according to the hosting platform. Never paste
secret values into an incident issue or status update.

## Production connection checklist

- [ ] Independent external probes cover the public page, authenticated health,
  generation without a real provider charge where possible, and export path.
- [ ] Metrics use durable, atomic, multi-instance storage with a documented
  retention/deletion schedule.
- [ ] Alert delivery reaches a monitored channel outside the affected service.
- [ ] P0 and P1 delivery, acknowledgement, escalation, deduplication, and
  recovery notifications are tested in the real hosting environment.
- [ ] Provider billing/usage is reconciled to D1 reservations.
- [ ] Dashboard access is least-privilege and audited.
- [ ] Status notices contain no customer identity, content, credentials, or
  unverified root-cause statements.

Until every item passes, the public status notice remains manual and the hosted
trial remains closed.
