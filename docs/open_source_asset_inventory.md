# Open-source asset inventory

> Review date: 2026-08-16
> Owner confirmation: project code and project evidence are original;
> evaluation brand and marketing candidates are AI-generated synthetic
> material, and the project social-preview image is AI-generated.

| Path | Content | Provenance | Public redistribution status | Release action |
|---|---|---|---|---|
| `src/`, `app/`, `web/`, `tools/` | Application and build source | Project-authored | Approved | Include |
| `prompts/` | Prompts, schemas, fixtures | Prompts and schemas are project-authored; evaluation fixtures are AI-generated synthetic material | Approved | Include; keep synthetic fixtures only |
| `data/products/` | Fictional SKU facts and cards | AI-generated synthetic brand material | Approved by owner | Include with `DATA_LICENSE.md` notice |
| `data/brand/` | Fictional brand, terminology, prohibited terms | AI-generated synthetic brand material | Approved by owner | Include with synthetic-brand notice |
| `data/insights/` | Structured insight and fact mappings | Project-authored project material | Approved by owner | Include; do not claim market representativeness |
| `data/evaluation/` | Synthetic candidates and evaluation records | AI-generated synthetic material | Approved by owner | Include with limitations and no-real-data notice |
| `data/measurements/` | Project measurements and scenario analysis | Project-authored | Approved | Include; preserve evidence labels |
| `data/platform_rules/` | Project rule summaries and external links | Project-authored summaries | Approved | Include; external pages remain third-party |
| `reports/` | Evaluation and validation reports | Project-authored | Approved | Include with sample-size limitations |
| `assets/` | Screenshots and project charts | Project-authored | Approved | Include |
| `web/public/og-portfolio.png` | Project social-preview image | AI-generated on 2026-08-16 with OpenAI's built-in image generation | Approved by owner | Include with explicit disclosure; never cite as evidence |
| `demo/` | Project video, PDF, and PPTX | Project-authored | Approved | Include; validate Release size |
| `outputs/` (if added) | Synthetic sample outputs | Must be project-authored or AI-generated synthetic material | Not present in current release candidate | Review before inclusion; never mix with user exports |

## Release checks

- Confirm no real customer data, private reviews, account identifiers, or
  personal information were added after the review date.
- Confirm all external rule links still point to official sources.
- Regenerate the dependency-license inventory for the exact release lockfiles.
- Check images, video, PDFs, and PPTX for hidden comments, author metadata,
  private paths, or credentials before publishing.
