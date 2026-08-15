# Changelog

All notable changes to LocalizeFlow will be documented in this file. The
project follows Semantic Versioning and uses prerelease identifiers while the
interfaces remain experimental.

## [Unreleased]

### Added

- Apache License 2.0 and repository notices.
- Reproducible Python project metadata and development dependencies.
- Continuous integration, CodeQL, and Dependabot configuration.
- Security, contribution, conduct, roadmap, issue, and pull request guidance.
- Data provenance and open-source asset inventory documentation.
- A process-local trial guard with account/project/client quotas, sliding-window
  rate limits, conservative cost reservations, HMAC-pseudonymous usage events,
  and repeated-rejection alerts.

### Changed

- Renamed the Web package from its starter-template name.
- Clarified that the hosted experience is an interactive deterministic Demo,
  not a production free trial.
- Upgraded Web dependencies and constrained transitive packages to remove
  known production dependency advisories found during the release audit.
- Expanded the Web release gate to audit development/build dependencies and
  removed all known high-severity advisories from the supported dependency tree.
- Corrected four screenshot extensions so file names match their JPEG format.
- Tightened Closed Beta product-listing output to require exactly five bullets,
  prevent internal fact-ID leakage, and keep brand-tone metadata out of claims.
- Corrected Mexican Spanish pump-bottle matching so `frasco con bomba` is not
  misclassified as a jar, with prompt/schema/rule versions advanced for auditability.
- Added deterministic claim-location coverage and verbatim-excerpt checks so
  claim inventories cannot point to missing or unrelated consumer copy.
- Added target-language blocking for consumer copy, withheld unusable fact
  values from generation inputs, and limited invalid fact-ID recovery to one
  targeted repair before a structured `insufficient_information` fallback.
- Expanded request-cost estimation to cover the initial generation, one
  semantic repair, and configured provider retries; cached results do not
  consume additional trial quota.

## [0.1.0-preview.1] - 2026-08-14

First open-source preview. The release date will be set only after the release
candidate passes the clean-environment checklist.

[Unreleased]: https://github.com/zugzwang-zg/LocalizeFlow/compare/v0.1.0-preview.1...HEAD
[0.1.0-preview.1]: https://github.com/zugzwang-zg/LocalizeFlow/releases/tag/v0.1.0-preview.1
