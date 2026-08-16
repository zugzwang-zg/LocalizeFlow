# Strategy A portfolio experience readiness

> Review date: 2026-08-16
> Scope: recruiter-facing Web information architecture and visual system
> Local status: ready for owner acceptance
> Hosted status: not published; the current public Demo is unchanged

## Product decision

Strategy A keeps the deterministic public Demo and uses the available effort
to make the portfolio evidence easier to understand. It does not reopen the
hosted free-trial scope. The page is designed for recruiters and hiring
managers evaluating AI product, localization technology, or full-stack
prototype work.

The intended reading path is:

1. Understand the product thesis and release boundary in roughly 30 seconds.
2. Reach the evaluation evidence and sample size within 90 seconds.
3. Distinguish the owner's contribution, product decisions, and limitations
   before entering the five-step Demo.
4. Use the Demo to inspect traceability, issue handling, and export gates.

## What changed

- The first viewport now identifies the work as a solo portfolio case study and
  separates `PUBLIC DEMO READY` from `FREE TRIAL NO-GO`.
- A release-manifest route makes the workflow legible as
  `FACTS -> LOCALIZE -> GATE -> EXPORT`.
- The evidence summary exposes the frozen 30-case comparison, review-time and
  revision-count changes, and the 5 SKU x 2 market x 3 content-type matrix.
- `WHAT I OWNED` separates product scope, data/content systems, implementation,
  and evaluation/release decisions.
- Four product decisions explain why fact IDs precede generation, hard failures
  override scores, the public Demo is deterministic, and NO-GO remains visible.
- The limitations state that factual-pass performance remains imperfect, ten
  enhanced cases miss the threshold, evaluation used AI-assisted review, and
  the project has no real-user adoption or professional independent review.
- The Beta call to action registers interest only and does not imply access.

## Visual direction

The previous general editorial treatment is replaced by a cross-border
clearance-manifest system. The restrained palette uses manifest navy, signal
teal, pale blue-white, checkpoint yellow, and block red. Condensed technical
sans and monospaced utility labels make the interface feel like a release
docket rather than a generic SaaS landing page. Motion remains secondary and
is disabled when the operating system requests reduced motion.

## Evidence boundaries

- The public Demo uses frozen fictional SKU data and deterministic outputs.
- It does not call a model API or accept real customer data.
- Evaluation material is AI-generated synthetic content; evaluation includes
  AI-assisted review and project-author adjudication, not professional
  independent review.
- `30/30` refers to paired wins under the frozen project evaluation protocol;
  it is not a production adoption, revenue, or platform-approval metric.
- The hosted free-trial release decision remains `NO-GO`.

## Social-preview asset provenance

`web/public/og-portfolio.png` is an AI-generated visual communication asset,
not project evidence. It was generated on 2026-08-16 with OpenAI's built-in
image generation and is redistributed with the disclosure in
`DATA_LICENSE.md`, `THIRD_PARTY_NOTICES.md`, and the open-source asset
inventory.

Generation prompt:

```text
Use case: ads-marketing
Asset type: landscape social sharing card for the LocalizeFlow portfolio website, 1536x1024 proportion
Primary request: Create a polished graphic that looks like a cross-border content clearance manifest, not a generic SaaS gradient card.
Scene/backdrop: clean pale blue-white technical document surface with a deep manifest-navy panel and precise customs/quality-control registration marks.
Subject: a four-stage horizontal clearance route with checkpoints for facts, localization, gate, and export; a small evidence ledger motif; no people and no product photography.
Style/medium: crisp editorial information design, screen-print precision, restrained and professional, inspired by shipping manifests and QA release documents without imitating any real government document.
Composition/framing: landscape, strong left-aligned title, route across the middle, status stamps on the lower right, ample safe margins for social cropping.
Color palette: manifest navy #13283A, signal teal #0B7A75, pale blue-white #F3F7F8, checkpoint yellow #F0C75E, block red #C84C3A.
Text (verbatim): "LocalizeFlow"; "EVIDENCE-LED LOCALIZATION DESK"; "FACTS  ->  LOCALIZE  ->  GATE  ->  EXPORT"; "PUBLIC DEMO · READY"; "FREE TRIAL · NO-GO"; "5 SKU · 2 MARKETS · 3 CONTENT TYPES".
Typography: condensed technical sans for the title, compact monospaced utility labels, high legibility at thumbnail size.
Constraints: render every listed text string exactly as written; one cohesive finished card; no logos other than the LocalizeFlow wordmark; no invented metrics; no Chinese text; no mock browser frame; no gradients; no rounded SaaS cards; no watermark.
```

## Acceptance gate

Before publication, the exact candidate must pass Web build, lint, tests,
dependency audit, repository validation, and the existing free-trial
fail-closed checks. The project owner must accept this local stage before the
existing Sites project is updated. Publication must not enable authentication,
uploads, model calls, or hosted export.
