# LocalizeFlow Web Demo

Browser-native version of the LocalizeFlow five-step workflow.

This is a free browser-local trial, not a hosted account or production service.
People can use the included examples or import the provided CSV/XLSX template.
Imported files stay in the current browser page and must not contain personal,
customer, confidential, or production data.

- Uses the included sample product library and evaluation content.
- Supports US English and Mexican Spanish.
- Reads CSV/XLSX files and runs checks and CSV/JSON exports in the browser.
- Does not upload imported files or call an online model service.

Run locally with `pnpm dev`; validate with `pnpm lint`, `pnpm test`,
`pnpm build`, and `pnpm security:audit`.

The build uses a project-owned, restricted `image-size` compatibility package
for static metadata. It supports PNG, JPEG, GIF, WebP, ICO, BMP, and SVG and
rejects ICNS, JXL, HEIF, and unknown formats before parsing.
