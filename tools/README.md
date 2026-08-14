# Release asset tools

The application and tests do not require these optional release-asset tools.

## Presentation source status

`build_project_overview_ppt.js` is retained as source reference, but its
optional `pptxgenjs` dependency is intentionally not included in the supported
release environment. At the 2026-08-14 audit, the latest package resolved an
`image-size` dependency with unresolved high-severity denial-of-service
advisories. Do not process untrusted images with that toolchain. The reviewed
PPTX remains directly editable in compatible presentation software.

## Rebuild the demonstration video

The locked Python development environment includes `imageio-ffmpeg`. Install
Poppler so `pdftoppm` is available, or point `PDFTOPPM` to its executable, then
run:

```powershell
uv run python tools\build_demo_video.py
```

The script renders the reviewed PDF and updates
`demo/LocalizeFlow_Demo.mp4`. Do not include generated QA frames in a release.
