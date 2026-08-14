# Open-source preview readiness report

**Candidate:** `v0.1.0-preview.1`
**Audit date:** 2026-08-14
**Status:** local release candidate passed; GitHub activation and publication
remain pending maintainer approval.

## Completed locally

- Added Apache License 2.0, NOTICE, data/material notices, and an asset
  inventory based on the project owner's provenance confirmation.
- Disclosed that the fictional brand, SKUs, product facts, marketing content,
  and evaluation materials are AI-generated synthetic content.
- Added reproducible Python metadata, supported runtime versions, development
  dependencies, and frozen Python/Web lockfiles.
- Added CI for Python 3.11–3.13 and Web, CodeQL, Dependabot, issue forms, a pull
  request template, security policy, contribution guide, conduct policy,
  roadmap, changelog, and release notes.
- Corrected four screenshot extensions so their names match their JPEG bytes.
- Pinned GitHub Actions to reviewed full commit SHAs.

## Verification results

| Gate | Result |
|---|---|
| Python startup smoke test | Passed |
| Python unit tests | 40 passed |
| Python coverage gate | 71%, minimum 70% |
| Ruff | Passed |
| mypy | Passed across `src/` and `app/` |
| Offline prompt/schema validation | 5 schemas, 9 prompts, 0 API calls; passed |
| Web lint | Passed with zero warnings |
| Web tests | 2 passed |
| Web production build | Passed |
| Python dependency audit | No known vulnerabilities after upgrading pytest |
| Web production dependency audit | No known vulnerabilities after upgrades and overrides |
| Worktree and full-history credential pattern scan | No candidate secrets |
| PPTX validation | Passed; notes reviewed; no private content found |
| PDF validation | 8 pages rendered and visually reviewed; no attachments, forms, JavaScript, encryption, or private author value found |
| Video validation | 144-second H.264/AAC file decoded; only encoder metadata found |
| Screenshot metadata | No EXIF fields; formats now match extensions |
| XLSX validation | 7 workbooks; no comments, hidden sheets, external links, external formulas, or personal author values |
| Python source/wheel build | Passed; LICENSE and NOTICE included (artifacts are audit-only, not release attachments) |

## License observations

- Reviewed Python and Web dependency license inventories contain common
  permissive licenses. The platform-specific Sharp binary declares
  `Apache-2.0 AND LGPL-3.0-or-later`; it remains a dynamically consumed npm
  dependency and is not relicensed by this repository.
- The optional PPT source generator is excluded from the supported dependency
  set because the latest `pptxgenjs` release resolves an `image-size` version
  with unresolved high-severity advisories. The validated PPTX remains
  directly editable; the source script must not process untrusted images.
- External Google and TikTok pages are linked, not copied. Names are used only
  to identify rule sources; no endorsement is claimed.
- Contributor Covenant attribution is preserved in `CODE_OF_CONDUCT.md` and
  `THIRD_PARTY_NOTICES.md`.

## Pending GitHub-side activation

The source repository is already public, but its current `main` branch does
not yet contain this candidate and GitHub reports no recognized license or
security policy. After maintainer acceptance:

1. push the candidate through a pull request;
2. observe CI and CodeQL on GitHub-hosted runners;
3. enable Private vulnerability reporting, Dependabot alerts/security updates,
   secret scanning and push protection;
4. create the documented labels and protect `main`;
5. set the changelog date, tag the reviewed commit, and publish the prerelease;
6. re-download and smoke-test the public source archive.

Exact operator steps are in `docs/maintainer_release_checklist.md`.

## Product risks carried into Stage B

- Packaging facts remain the largest known fact-error category and require a
  structured hard gate before the public interactive Demo milestone.
- Evaluation has one reviewer and a small synthetic sample; results are not
  evidence of statistical significance or production performance.
- The deterministic Demo is intentionally not described as a free trial.

No Stage B implementation is included in this release candidate.
