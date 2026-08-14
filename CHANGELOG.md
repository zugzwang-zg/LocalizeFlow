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

### Changed

- Renamed the Web package from its starter-template name.
- Clarified that the hosted experience is an interactive deterministic Demo,
  not a production free trial.
- Upgraded Web dependencies and constrained transitive packages to remove
  known production dependency advisories found during the release audit.
- Expanded the Web release gate to audit development/build dependencies and
  removed all known high-severity advisories from the supported dependency tree.
- Corrected four screenshot extensions so file names match their JPEG format.

## [0.1.0-preview.1] - 2026-08-14

First open-source preview. The release date will be set only after the release
candidate passes the clean-environment checklist.

[Unreleased]: https://github.com/zugzwang-zg/LocalizeFlow/compare/v0.1.0-preview.1...HEAD
[0.1.0-preview.1]: https://github.com/zugzwang-zg/LocalizeFlow/releases/tag/v0.1.0-preview.1
