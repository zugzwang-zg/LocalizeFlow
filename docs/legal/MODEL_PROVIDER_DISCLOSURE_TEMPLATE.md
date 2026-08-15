# Model and relay disclosure record

Status: release-blocking template; not a completed disclosure

Last reviewed: 2026-08-15

Complete this record from the provider's current contract, DPA, privacy terms,
security documentation, and account settings. A working API key or successful
smoke test is not evidence for the legal or privacy fields below. Attach dated
screenshots or exported settings to the private release evidence folder.

## Deployment

| Required field | Verified value | Evidence and review date |
|---|---|---|
| Hosted operator/legal entity | `[REQUIRED]` | `[REQUIRED]` |
| Application hosting provider and region | `[REQUIRED]` | `[REQUIRED]` |
| Database/object-storage provider and region | `[REQUIRED]` | `[REQUIRED]` |
| Backup location and purge period | `[REQUIRED]` | `[REQUIRED]` |

## Relay or intermediary

| Required field | Verified value | Evidence and review date |
|---|---|---|
| Legal entity and registered address | `[REQUIRED]` | `[REQUIRED]` |
| Product/API name and contract owner | `[REQUIRED]` | `[REQUIRED]` |
| Privacy notice, terms, DPA, and subprocessor list | `[REQUIRED]` | `[REQUIRED]` |
| API processing and log regions | `[REQUIRED]` | `[REQUIRED]` |
| Input/output retention and deletion route | `[REQUIRED]` | `[REQUIRED]` |
| Training or service-improvement use | `[REQUIRED: must be no for user data]` | `[REQUIRED]` |
| Human access and abuse-monitoring conditions | `[REQUIRED]` | `[REQUIRED]` |
| Security and incident contact | `[REQUIRED]` | `[REQUIRED]` |
| Downstream model provider(s) | `[REQUIRED]` | `[REQUIRED]` |

## Model provider and model

| Required field | Verified value | Evidence and review date |
|---|---|---|
| Model provider legal entity | `[REQUIRED]` | `[REQUIRED]` |
| Exact model/API version | `[REQUIRED]` | `[REQUIRED]` |
| Privacy notice, terms, DPA, and subprocessor list | `[REQUIRED]` | `[REQUIRED]` |
| Processing and storage regions | `[REQUIRED]` | `[REQUIRED]` |
| Input/output retention and deletion route | `[REQUIRED]` | `[REQUIRED]` |
| Training or service-improvement use | `[REQUIRED: must be no for user data]` | `[REQUIRED]` |
| Human access and abuse-monitoring conditions | `[REQUIRED]` | `[REQUIRED]` |
| Security and incident contact | `[REQUIRED]` | `[REQUIRED]` |

## Transfer and user disclosure

- Data route, in order: `[REQUIRED: browser/app → hosting → relay → model → return]`
- Countries/regions at every hop: `[REQUIRED]`
- Transfer mechanism or other legal basis where applicable: `[REQUIRED]`
- Categories sent: `[REQUIRED]`
- Categories deliberately excluded: `[REQUIRED]`
- In-product notice location and exact confirmation text: `[REQUIRED]`
- Alternative path when a user declines: `[REQUIRED]`

## Approval

- Technical owner and date: `[REQUIRED]`
- Privacy/legal reviewer and date: `[REQUIRED]`
- Configuration evidence matches production: `[REQUIRED: yes/no]`
- Re-review trigger/date: `[REQUIRED]`

Do not enable hosted model processing while any field is unresolved, the
evidence is stale, or production configuration differs from this record.
