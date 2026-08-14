# LocalizeFlow Closed Beta protocol

Status: internal candidate; not yet accepting real data  
Version: 0.1  
Owner: project maintainer  
Planned duration: four weeks

## Scope

- 5–10 invited cross-border ecommerce content operators.
- 1–3 authorized SKUs per participant; target at least 10 completed SKUs overall.
- Beauty and personal care only.
- en-US and es-MX only.
- Product listing, 15-second video script, and social ad copy.
- File export only. The Beta does not connect to or publish on a commerce or advertising platform.
- Every output requires fact, rule, target-language, and participant sign-off.

Out of scope: medical devices, prescription or therapeutic claims, children-directed products, ingestible products, regulated financial claims, real customer lists, personal data, production credentials, and automatic publishing.

## Participant criteria

Participants must:

1. Work directly with cross-border product content or review.
2. Have authority to upload the selected product data and permit processing by the disclosed model provider and relay.
3. Be able to provide a current source for every product fact and claim.
4. Join one 30-minute onboarding and one 30-minute interview each week.
5. Agree not to publish unreviewed output or use the Beta for high-risk decisions.

## Recruitment and approval

1. Applicant submits the public Beta form without product content.
2. Maintainer checks role, use case, market, language, product category, and data authority.
3. Maintainer explains the data flow, model/relay provider, retention, deletion, security limits, and incident contact.
4. Participant signs the approved Beta agreement and, when required, a separate NDA or data-processing addendum reviewed by counsel.
5. Maintainer creates one isolated participant project and records the participant ID, project ID, approval date, allowed markets, and expiry date.
6. Product files are accepted only after access and deletion controls pass the preflight checklist.

## Project isolation

- One participant may access only projects explicitly assigned to their stable authenticated user ID.
- Project and file authorization is checked server-side for every read, write, export, and delete operation.
- D1 stores ownership and workflow metadata; R2 stores upload bytes only when hosted persistence is enabled.
- Public Demo data and Beta project data never share tables, storage prefixes, exports, or logs.
- A local development session is not considered tenant isolation and must not be used for a hosted Beta.

## Test cadence

| Week | Task | Evidence |
|---|---|---|
| 0 | Consent, access, safe-upload rehearsal | signed approval, access test, deletion test |
| 1 | First SKU: import, fact confirmation, generation | baseline time, LocalizeFlow time, gate log |
| 2 | Second task or market | corrections, failure categories, interview notes |
| 3 | Independent en-US / es-MX review | two reviewer records, disagreements |
| 4 | Final task and adoption interview | usability decision, blockers, priority list |

## Withdrawal and deletion

- Participants may withdraw at any time through the designated private support channel.
- New processing stops when withdrawal is received.
- Active project data is deleted within seven calendar days unless a shorter legal or contractual period applies.
- Backups, if introduced, must document a maximum purge period before Beta launch.
- Deletion produces an audit record containing only project ID, deletion time, actor, and result; it must not retain content.
- Aggregate metrics may be retained only when they cannot identify the participant, brand, SKU, or content.

## Publication and confidentiality

Real participant data, screenshots, outputs, quotes, company names, and results are private by default. Nothing may be added to the public repository, Demo, marketing page, report, or presentation without separate written permission that identifies the exact material and intended use.

## Stop conditions

Pause the Beta immediately for cross-tenant access, a secret or personal-data leak, a critical fact contradiction passing the export gate, uncontrolled model cost, a missing deletion path, or an undisclosed change to the model/relay data flow.
