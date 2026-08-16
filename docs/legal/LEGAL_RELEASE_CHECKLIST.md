# Legal and privacy release checklist

Status: hosted trial blocked

Last evidence review: 2026-08-15

This checklist is product-release evidence, not legal advice or a declaration
of compliance. Applicability depends on the operator, users, data, processing
locations, and markets. Obtain qualified review where the deployment requires
it.

## Current truthful boundary

- [x] The public deterministic Demo has a scoped privacy notice and does not
  call a model API or automatically transmit local metrics.
- [x] Preview terms, acceptable use rules, fictional-data disclosure, and
  prominent professional/platform disclaimers are published in the repository.
- [x] The model data policy makes no-training use the default product
  requirement and blocks user-data calls when it cannot be verified.
- [x] Hosted privacy and terms templates are marked `NOT ACTIVE`.
- [ ] A hosted free trial is approved to accept registrations or uploads.

## Hosted operator and contacts — all required before launch

- [ ] Legal operator/controller name, address, and country are approved.
- [ ] Dedicated privacy request channel is tested end to end.
- [ ] Security incident channel is private, monitored, and tested.
- [ ] Support and legal-notice contacts and response ownership are assigned.
- [ ] Offered jurisdictions, minimum age, contracting authority, governing law,
  consumer-rights treatment, and dispute terms are reviewed.

## Processing inventory and user rights

- [ ] Every production data category has a documented purpose, applicable legal
  basis/permitted purpose, recipient, source, retention period, and deletion
  route.
- [ ] Notice at collection appears before account creation and upload where
  required, and matches the full privacy notice.
- [ ] Access, correction, deletion, restriction, portability, objection,
  consent withdrawal, appeal, and regulator-complaint routes are mapped for the
  jurisdictions where each applies.
- [ ] Identity verification, authorized-agent handling, response deadlines,
  exceptions, and non-discrimination are documented and rehearsed.
- [ ] Primary stores, caches, failed imports, logs, support systems, and backups
  have tested deletion or an approved exception.

## Providers, regions, and transfers

- [ ] `MODEL_PROVIDER_DISCLOSURE_TEMPLATE.md` has no `[REQUIRED]` fields.
- [ ] Hosting, database, object storage, relay, model, email/support, monitoring,
  and backup providers and subprocessors are disclosed.
- [ ] Processing/logging regions, international data routes, and applicable
  transfer safeguards are documented from current evidence.
- [ ] Provider terms, DPA, retention, deletion, human access, abuse monitoring,
  incident handling, and subprocessor-change process are approved.
- [ ] Production settings enforce no training or provider improvement using
  uploaded data, prompts, outputs, or edits.
- [ ] A provider/region/route change disables processing until disclosure and
  approval are refreshed.

## User content and high-risk boundaries

- [x] Terms require users to hold rights and permissions for uploaded material.
- [x] The acceptable use policy excludes sensitive data in the public Demo,
  deceptive or unsubstantiated claims, high-impact decisions, abuse, and
  security/limit bypass.
- [x] The disclaimer distinguishes automated checks from medical, legal,
  regulatory, translation, scientific, and platform approval.
- [ ] Production onboarding records the user's upload authorization and the
  disclosed model/relay transfer confirmation.
- [ ] Suspension, appeal, evidence preservation, legally required reporting,
  and repeat-abuse operations are implemented and tested.

## Production-document approval

- [ ] Every placeholder in `HOSTED_TRIAL_PRIVACY_DRAFT.md` is replaced and the
  final notice matches measured production behavior.
- [ ] Every placeholder in `HOSTED_TRIAL_TERMS_DRAFT.md` is replaced and the
  final terms match actual quotas, support, suspension, export, and deletion.
- [ ] Version, effective date, prior-policy archive, change-notice method, and
  acceptance evidence are implemented.
- [ ] Appropriate privacy/legal reviewer approval and evidence date are recorded.
- [ ] A final red-team review finds no claim that the service is compliant,
  secure, private, approved, or no-training beyond the evidence.

## Authoritative research starting points

Verified accessible on 2026-08-15. These sources inform the fields above but do
not determine which law applies to a future deployment.

- [EU General Data Protection Regulation, especially Article 13](https://eur-lex.europa.eu/legal-content/EN/TXT/?qid=1521391131953&uri=CELEX%3A32016R0679): controller/contact, purposes and legal basis, recipients, international transfers, retention, rights, and complaint information.
- [European Commission — information for individuals](https://commission.europa.eu/law/law-topic/data-protection/information-individuals_en): transparent notice and data-subject rights overview.
- [California Attorney General — California Consumer Privacy Act](https://oag.ca.gov/privacy/ccpa): notice at collection and California consumer rights, subject to statutory applicability.
- [China Ministry of Industry and Information Technology — Personal Information Protection Law](https://www.miit.gov.cn/jgsj/zfs/fl/art/2022/art_515a4b20c12f430eab54bb4f56d89f56.html): personal-information processing and cross-border provisions.
- [Mexico Chamber of Deputies — Federal Law on Protection of Personal Data Held by Private Parties](https://www.diputados.gob.mx/LeyesBiblio/ref/lfpdppp.htm): official current-law and reform record.
- [US Federal Trade Commission — Health Products Compliance Guidance](https://www.ftc.gov/business-guidance/resources/health-products-compliance-guidance): truthful, non-misleading express and implied health claims and competent substantiation.
- [UK Information Commissioner's Office — right-to-be-informed checklist](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/the-right-to-be-informed/checklists/): operational notice checklist for UK GDPR deployments.

Recheck the current text, applicability, regulator guidance, and provider terms
immediately before any hosted launch; links and requirements can change.
