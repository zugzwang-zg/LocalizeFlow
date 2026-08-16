# Operations document map

Last updated: 2026-08-16

- `MONITORING_AND_ALERTING.md`: metric definitions, privacy boundary,
  thresholds, alert ownership, and production gaps.
- `INCIDENT_RESPONSE.md`: P0/P1/P2 declaration, containment, communication,
  recovery, and post-incident workflow.
- `RELEASE_RUNBOOK.md`: pre-release gate, smoke/regression commands, emergency
  switches, rollback, and release evidence.
- `INCIDENT_TEMPLATE.md`: content-free incident record and postmortem template.

The repository implements a process-local reference monitor for deterministic
tests. It does not claim production availability. A hosted trial remains
blocked until metrics are durable across instances, independent probes and an
external alert destination are connected, and delivery/on-call drills pass in
the actual deployment.
