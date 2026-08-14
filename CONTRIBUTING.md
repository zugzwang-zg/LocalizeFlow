# Contributing to LocalizeFlow

Thank you for helping improve LocalizeFlow. Contributions are welcome for
fact safety, localization quality, platform-rule maintenance, tests,
documentation, and accessibility.

## Before you start

1. Search existing issues and the roadmap.
2. Open an issue before substantial behavior, schema, or rule changes.
3. Never include real customer data, secrets, private reviews, or unlicensed
   product material in an issue, fixture, screenshot, or pull request.
4. Treat platform prechecks as assistance, not legal advice or approval.

## Development setup

Python 3.11–3.13 and Node.js 22.13 or later are supported.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install uv==0.12.4
.\.venv\Scripts\uv.exe sync --locked --extra dev
.\.venv\Scripts\uv.exe run pytest -q
```

```bash
cd web
pnpm install --frozen-lockfile
pnpm lint
pnpm test
pnpm security:audit
```

Run the Streamlit Demo with:

```powershell
.\.venv\Scripts\uv.exe run streamlit run app\main.py
```

## Pull request checklist

- Keep the change focused and link the relevant issue.
- Add or update tests for behavior changes.
- Record the source URL and verification date for platform-rule changes.
- Preserve old rule versions used by published evaluations.
- Explain any data, schema, prompt, or release-note impact.
- Run Python tests, Ruff, mypy, Web lint, Web tests/build, and the complete Web
  dependency audit.
- Do not replace a hard fact gate with an aggregate quality score.

## Commit and review guidance

Use clear imperative commit messages. Reviewers should be able to verify the
change without hidden local files or private services. A pull request must not
be merged while required checks fail.

By submitting a contribution, you agree that it is licensed under the
Apache License 2.0 and that you have the right to submit it.
