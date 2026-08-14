# LocalizeFlow Web Demo

Browser-native, deterministic version of the LocalizeFlow five-step workflow.

This is an interactive product Demo, not a production free trial. It accepts
only the repository's fictional sample data and must not be used for
confidential customer material.

- Uses the frozen project fact library and evaluation content.
- Supports US English and Mexican Spanish.
- Runs quality checks and CSV/JSON exports in the browser.
- Does not call a model API or require an API key.

Run locally with `pnpm dev`; validate with `pnpm lint`, `pnpm test`,
`pnpm build`, and `pnpm security:audit`.

The build uses a project-owned, restricted `image-size` compatibility package
for static metadata. It supports PNG, JPEG, GIF, WebP, ICO, BMP, and SVG and
rejects ICNS, JXL, HEIF, and unknown formats before parsing.
