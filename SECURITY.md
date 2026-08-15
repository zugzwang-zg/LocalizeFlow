# Security Policy

## Supported versions

LocalizeFlow is currently an alpha-stage reference implementation. Security
fixes are provided for the latest release on the `main` branch only.

| Version | Supported |
|---|---|
| Latest release | Yes |
| Older snapshots | No |

## Reporting a vulnerability

Do not open a public issue for vulnerabilities, exposed credentials, private
data, or instructions that would enable exploitation.

Use GitHub's **Private vulnerability reporting** feature on the repository
Security page. If that feature is temporarily unavailable, contact the
maintainer through the private contact method listed on the maintainer's
GitHub profile.

Please include:

- affected version or commit;
- affected component and deployment mode;
- reproduction steps or a minimal proof of concept;
- potential impact;
- suggested mitigation, if known.

The maintainer will acknowledge a complete report within 5 business days and
will coordinate disclosure after a fix or mitigation is available. Please do
not access data that is not yours, disrupt a live service, or publish details
before coordinated disclosure.

## Security boundaries

The public Demo uses fictional data and deterministic local processing. It is
not approved for confidential customer data. A future model-backed or hosted
version must add authentication, tenant isolation, retention controls, rate
limits, abuse prevention, and production monitoring before accepting real
product material.

The local Closed Beta gateway includes process-local account, project, and
client quotas plus daily/monthly cost reservations. Identifiers are stored as
HMAC-SHA256 digests. These controls are a testable safety primitive, not a
production security boundary: the local client key is session-generated, the
store resets on process restart, and no trusted reverse-proxy IP adapter or
external alert destination exists. See `docs/trial_limits.md`.

The optional local tenant store adds scrypt password hashing, expiring
in-memory sessions, encrypted account/project content, server-side tenant
filters, self-service export, and destructive project/account deletion. It does
not provide hosted HTTPS, email verification, MFA, password recovery, managed
KMS, encrypted backups, or multi-instance authorization. See
`docs/tenant_isolation.md` before evaluating this code for hosted use.
