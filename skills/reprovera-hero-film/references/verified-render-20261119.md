# Verified reproducibility record — 2026-11-19

This is a record of a real, full rerender, not a mock or theoretical command.

- Source inputs: 14 original owner-approved prepared clips (7 desktop + 7 mobile), staged privately outside the central public repository and verified against examples/production-v8.json with SHA-256.
- Executed scripts/render_hero.py using --check --public-candidate and --render --public-candidate. FFmpeg 8.1.1, ffprobe 8.1.1, Python 3.11.15, Windows.
- Output: 7-scene H.264/x264 video without audio, 25fps, dissolve 1.12s, 29.12s duration.
- Desktop: 1280×720, 5,174,142 bytes, SHA-256 **b60584984d2f8bb083773f237c110d91f3d84827ccfebe9308b9c9340770e302**.
- Mobile: 540×960, 2,944,578 bytes, SHA-256 **bd494ce0da3d33b501227d3c96f87f991cc7971fd9b849a4377da178ef227034**.
- Both output digests **exactly matched** the previously approved and deployed ReproVera video files.
- Renderer unit tests: 4/4 PASS, including the medical-grade recipe, missing file, pending rights, source-hash tampering, and synthetic three-scene desktop/mobile pipeline.
- Central repository Node contracts: 22/22 PASS; TypeScript smoke compilation PASS; Agent Skills specification validation PASS.
- No real footage committed here. Exact output hashes are reference checks for this source set and FFmpeg version; a deliberate change of footage or encoder version can change encoded bytes.

In all later edits, reproduce first, change one approved variable at a time, compare source and output hashes, and report the difference rather than asserting a match.
