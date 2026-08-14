# Feedback operations

The public demo offers three explicit feedback paths: download a local structured feedback file, open a GitHub error report, or submit the public Beta application form. The demo never silently submits a content body.

## Intake fields

- SKU, market, content type
- useful / not useful
- category: localization, fact error, platform rule, or usability
- optional note
- content consent (off by default; applies only to the local download)
- owner, status, and submission timestamp

## Ownership and status

The project maintainer owns the intake queue. Use `new`, `triaged`, `planned`, `resolved`, or `declined`. Security reports must follow `SECURITY.md`, not a public issue.

## Weekly review

Once each week:

1. Review new GitHub feedback and Beta applications.
2. Remove or redact accidentally submitted sensitive information where repository permissions allow.
3. Merge duplicates and assign category, severity, owner, and target milestone.
4. Reproduce fact or rule failures against the frozen dataset and record the rule/fact IDs.
5. Move actionable items to `planned`; close non-actionable items with a reason.
6. Summarize counts, top failure modes, and median response time in the project log without copying user content.
