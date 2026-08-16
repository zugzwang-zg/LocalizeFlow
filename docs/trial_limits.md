# Trial quotas and cost protection

This document defines the local D1 safety controls for a future model-backed
trial. It does not authorize a public free trial.

## Funding decision

The configured mode is `owner_funded_capped`: the project owner supplies a
small promotional allowance and every call is subject to hard limits. The
product does not present a user-supplied API key as a free allowance, and it
does not silently switch between project-funded and user-funded calls.

Default local limits are deliberately small:

| Scope | Limit |
|---|---:|
| Completed billable generation runs per account per month | 3 |
| Completed billable generation runs per project per month | 3 |
| Languages used by one project | 2 |
| Account requests per 10 minutes | 3 |
| Project requests per 10 minutes | 3 |
| Client requests per 10 minutes | 5 |
| Account model budget per day | USD 0.10 |
| Global model budget per day | USD 1.00 |
| Global model budget per month | USD 10.00 |

These values are configuration defaults, not a commercial promise. A future
trial page must show the active allowance before a user submits data.

## Enforcement order

`run_limited_beta_generation` performs the following checks before contacting
the model provider:

1. Validate the provider configuration and conservative per-request ceiling.
2. Reject a duplicate in-progress idempotency key.
3. Check account, project, and client sliding-window request limits.
4. Check monthly account/project generation and project-language quotas.
5. Reserve the worst-case request cost against account-day, global-day, and
   global-month budgets.
6. Run the existing model, schema, fact, language, and packaging gates.
7. Replace the reservation with actual metered cost after success.

The worst-case reservation covers the initial generation, one semantic repair,
and configured provider retries. If a provider call fails without trustworthy
usage data, the reservation remains charged for that budget period. This
conservative choice can reduce availability, but prevents repeated ambiguous
failures from creating unbounded spend. Idempotent cache hits do not consume a
second quota or budget reservation. A structured `insufficient_information`
result still consumed a model call and therefore counts as a completed billable
run. If metered cost ever exceeds its reservation, actual cost is retained and
a critical local alert record is created.

When a limit is reached, the provider is not called. The UI displays a plain
limit message instead of silently retrying or creating additional cost.

## Abuse signals and privacy

Repeated rejected requests create a process-local warning record after the
configured threshold. Events store HMAC-SHA256 identifiers rather than raw
account, project, or client identifiers. The HMAC deployment secret must be at
least 32 characters and must not be committed.

The local Streamlit adapter uses a random session identifier as its client key.
It is not a trusted IP control. A hosted version must derive a stable HMAC token
from the authenticated account and a trusted reverse-proxy client address, and
must reject user-supplied forwarding headers.

## Production gaps

The current store is process-local and resets after restart. It is suitable for
tests and a single-process portfolio demonstration, not for a public trial.
Before public access, D2 and D4 must provide:

- authenticated account and tenant identifiers;
- a trusted client/IP adapter at the deployment edge;
- durable, atomic, multi-instance quota and reservation storage;
- an external alert destination and on-call procedure;
- reconciliation against provider billing/usage records;
- administrative pause and budget-reset controls;
- retention and deletion rules for pseudonymous usage events.

Until those controls are implemented and rehearsed, keep the model-backed trial
private and disabled in public deployments.
