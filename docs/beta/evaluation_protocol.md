# Closed Beta evaluation protocol

## Objective

Determine whether LocalizeFlow reduces review effort without allowing critical fact contradictions to pass the export gate, and whether invited operators want to continue using it.

## Unit of analysis

One task is one authorized SKU × one market × one content type. en-US and es-MX results are reported separately before any combined summary.

## Baseline and LocalizeFlow timing

1. Start the Baseline timer before the participant begins the same task manually with their normal tools.
2. Stop when the participant considers the file ready for the same final review standard.
3. Reset the task context where practical, then start the LocalizeFlow timer before import.
4. Include import, fact confirmation, generation, correction, gate handling, and export in LocalizeFlow time.
5. Record interruptions separately and exclude only when the rule is applied consistently to both conditions.
6. Count substantive modifications that change factual accuracy, terminology, tone, structure, or usability; do not count cursor movement or formatting clicks.

## Independent language review

- Assign at least two qualified reviewers for the target language.
- Blind candidate identity when comparing outputs.
- Reviewers score independently before discussion.
- Use 1–5 scores for factual accuracy, terminology, fluency, brand fit, and platform fit.
- Separately record usability and whether a critical fact contradiction is present.
- Do not average away a critical contradiction. One verified contradiction past the export gate triggers the stop condition.
- When reviewers disagree materially, a third reviewer adjudicates and records the reason without overwriting original scores.

## Required outputs

- Per-task Baseline and LocalizeFlow duration.
- Modification count and final usability.
- Gate failures by fact, packaging, rule, language, and model category.
- Two independent review records per task.
- Reviewer disagreement and adjudication record.
- en-US and es-MX tables.
- Weekly adoption willingness, blockers, and top requests.

## Stage C hard targets

- At least 10 authorized real SKUs complete the end-to-end workflow.
- Two independent target-language reviews per completed task.
- Zero critical fact contradictions pass the export gate.
- Every model run records model, prompt, schema, rule versions, fact IDs, tokens, latency, cost estimate, and outcome.
- Product adoption decision and prioritized blockers are documented.

Efficiency and score improvements are reported with sample size and range. They are not described as statistically significant unless the study design and sample support that claim.
