# LocalizeFlow v0.1.0-preview.1

LocalizeFlow v0.1.0-preview.1 is the first open-source preview of an
evidence-first workflow for cross-border product content localization.

## What is included

- A five-step Streamlit Demo covering product facts, task configuration,
  deterministic content candidates, quality checks, human review, and export.
- A browser-native Web Demo built from the same frozen fictional scenario.
- Fact and rule checkers with tests for export gates and high-risk claims.
- Prompts, schemas, synthetic evaluation fixtures, reports, and editable
  presentation assets.
- Apache-2.0 licensing, provenance notices, contributor guidance, security
  reporting, CI, CodeQL, and Dependabot configuration.

## Important boundaries

- This release uses an AI-generated fictional brand, SKUs, product facts,
  marketing candidates, and evaluation material. It contains no real customer
  catalog.
- The Demo is deterministic and does not call a model API.
- It is not a production free trial and does not accept confidential data.
- Automated checks do not constitute platform approval, legal advice,
  medical evidence, or professional target-language review.
- Known product limitation: packaging facts require stronger structured hard
  gates before the project advances to a public interactive Demo release.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install uv==0.12.4
.\.venv\Scripts\uv.exe sync --locked --extra dev
.\.venv\Scripts\uv.exe run pytest -q
.\.venv\Scripts\uv.exe run streamlit run app\main.py
```

```bash
cd web
pnpm install --frozen-lockfile
pnpm lint
pnpm test
pnpm build
```

Read `DATA_LICENSE.md`, `THIRD_PARTY_NOTICES.md`, `SECURITY.md`, and
`reports/open_source_readiness.md` before redistributing or deploying the
preview.
