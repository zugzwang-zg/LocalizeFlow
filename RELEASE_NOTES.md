# LocalizeFlow v0.2.0-preview.1

LocalizeFlow v0.2.0-preview.1 turns the first open-source prototype into an
evidence-led portfolio release with structured packaging facts, hard quality
gates, a recruiter-facing public Demo, and explicit hosted-trial boundaries.

## Highlights

- A five-step public Web Demo for facts, market/task selection, evidence-bound
  content, issue localization and deterministic repair, human review, and
  audited export.
- Structured packaging facts and pre-generation, post-generation, and
  post-edit hard gates that reject unsupported or contradictory claims.
- A controlled local Closed Beta candidate with safe SKU import, fact
  confirmation, schema validation, tenant isolation, conservative quotas,
  cost reservations, emergency switches, and content-free audit metrics.
- Public privacy, terms, acceptable-use, disclaimer, status, support, security,
  incident, release, rollback, and hosted-trial prerequisite documentation.
- A recruiter-oriented portfolio readout that separates product contribution,
  evaluation evidence, key decisions, and known limitations.

## Evaluation snapshot

The frozen evaluation contains 5 fictional SKUs, 2 markets, and 3 content
types: 30 A/B pairs and 60 anonymous candidates.

| Metric | Baseline | LocalizeFlow |
|---|---:|---:|
| A/B paired wins | 0/30 | 30/30 |
| Average review time | 6.33 min | 4.70 min (-25.8%) |
| Average revisions | 3.63 | 1.40 (-61.5%) |
| Factual pass rate | 40.0% | 66.7% |
| Threshold failures | 20 | 10 |

These results apply only to the frozen project protocol. Evaluation used
AI-assisted review and project-author adjudication; it is not professional
independent review, statistical significance, user adoption, revenue, or proof
of platform approval.

## Important boundaries

- The public Demo uses frozen AI-generated fictional content, runs
  deterministically, does not call a model API, and does not accept real
  customer data.
- The hosted free-trial decision remains **NO-GO**. Registration, uploads,
  user-data model calls, server-side persistence, and hosted export are closed.
- Eleven hosted production prerequisites remain **UNRESOLVED**, including the
  operator, provider/data terms, hosted identity/storage, durable quotas,
  backup/deletion, external monitoring, rollback, and real support coverage.
- Automated checks do not constitute platform approval, legal advice, medical
  evidence, or professional target-language review.
- `web/public/og-portfolio.png` is an AI-generated communication asset, not
  evaluation or product-performance evidence.

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

Public Demo: <https://localizeflow-demo-86182.reidmozzie.chatgpt.site>

Before redistributing or deploying, read `DATA_LICENSE.md`,
`THIRD_PARTY_NOTICES.md`, `SECURITY.md`, `DISCLAIMER.md`, and
`reports/open_source_release_candidate.md`.
