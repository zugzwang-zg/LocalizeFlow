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
