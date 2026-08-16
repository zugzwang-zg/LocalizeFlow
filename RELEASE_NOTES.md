# LocalizeFlow v0.2.0-preview.2

LocalizeFlow v0.2.0-preview.2 is a security-only follow-up to the first 0.2.0
portfolio preview. It preserves the same deterministic public Demo and product
behavior while updating the Python cryptography dependency used by the optional
local encrypted tenant store.

## Security update

- Upgrades `cryptography` from 46.0.7 to 50.0.0.
- Addresses [GHSA-537c-gmf6-5ccf](https://github.com/advisories/GHSA-537c-gmf6-5ccf),
  [GHSA-g6cj-pr64-35w5](https://github.com/advisories/GHSA-g6cj-pr64-35w5),
  [GHSA-jwv3-5hgf-82ww](https://github.com/advisories/GHSA-jwv3-5hgf-82ww), and
  [GHSA-m2h6-j472-rp4c](https://github.com/advisories/GHSA-m2h6-j472-rp4c).
- Adds a machine gate that requires the patched dependency range in both
  requirement files and version 50.0.0 in `uv.lock`.

The immutable `v0.2.0-preview.1` tag remains available for traceability but is
superseded by this security patch. New downloads and evaluations should use
`v0.2.0-preview.2` after it is formally published.

## Verification snapshot

- The dependency-only update changed `pyproject.toml`, `requirements.txt`, and
  `uv.lock`.
- Python 3.11, 3.12, and 3.13 CI, Web CI, and Python/JavaScript CodeQL passed.
- An independent Windows Python 3.12 environment installed cryptography 50.0.0
  from the frozen lock; 141 tests plus 6 subtests, Ruff, mypy, prompt validation,
  startup smoke, and the operations drill passed at 72.22% coverage.
- An audit of the installed verification environment found no known
  vulnerabilities. GitHub Dependabot, Code Scanning, and Secret Scanning open
  alert counts returned zero after the dependency graph refreshed.
- No model API calls were made.

## Unchanged boundaries

- The public Demo uses frozen AI-generated fictional content, is deterministic,
  does not call a model API, and does not accept real customer data.
- The hosted free-trial decision remains **NO-GO** and all eleven hosted
  production prerequisites remain **UNRESOLVED**.
- Registration, real-data uploads, hosted model calls, server-side persistence,
  and hosted export remain closed.
- Automated checks do not constitute platform approval, legal advice, medical
  evidence, or professional target-language review.

Public Demo: <https://localizeflow-demo-86182.reidmozzie.chatgpt.site>

Before redistributing or deploying, read `DATA_LICENSE.md`,
`THIRD_PARTY_NOTICES.md`, `SECURITY.md`, `DISCLAIMER.md`, and
`reports/open_source_release_candidate.md`.
