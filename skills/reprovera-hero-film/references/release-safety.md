# Release discipline and verification checklist

ReproVera is a public health-information service with separate Account/Passport, Journal, and clinical integrations. A hero-video change must not roll back unrelated code.

## Before editing

1. Find the currently deployed worker/version, *the production-matched Git tree*, the full V8 hero video, and canonical source page. Never guess the latest approved state from git main; check SHA-256 of public files against local tree.
2. Record the original desktop and mobile MP4 SHA-256. Save immutable copies or point to existing originals; do not overwrite. Keep all edits on a new branch/worktree and in a new preview output directory.
3. Verify per-clip provenance, consent, any identifiable people or personal health data, advertising implications, stock restrictions and license compatibility. License unknown/pending is a hard public STOP. A user saying a clip is theirs can establish user-provided provenance for that specific file, but not for different external YouTube videos.
4. For every CC BY scene preserve author, title, source URL, license URL, and clear disclosure of speed/crop/colour/edit changes in the public methodology or comparable accessible credit.

## Frame and audio QA

- Keep correct clinical causality. ICSI should visibly show the micropipette entering the oocyte; embryo cleavage footage must be actual microscopy, not simulated growth.
- No sound; audio codec must be absent, muted playback does not make an accidentally encoded audio track acceptable.
- ffprobe: H.264, yuv420p, 25fps, duration approximately 29.12s for the unchanged V8 scene list; desktop 1280×720 and mobile 540×960.
- Inspect the scene at start, midpoint, end and both ends of each of the six dissolves; pay particular attention to scene 04's microinjection and mobile crop.
- Subtle unified film palette, no aggressive pink tint, no loss of clinical details from blur; check compression artifacts and mobile bandwidth and playback.
- Test actual phone aspect ratio and at least Chromium + Firefox; respect prefers-reduced-motion and poster availability. Firefox-specific mobile stutter seen historically was intermittent; don't claim regression without reproducing it.

## Before production

- Owner approves the *final updated film* and explicitly authorizes public deployment; no implied approval because the user earlier approved V8.
- Verify production-matched baseline including scripts and asset hashes (Account, Passport, Journal, nav, consent, ICSI). Verify current Worker bindings and secrets remain intact. Diff HTML/JS/CSS and compare sitemap.
- Update src/site/homepage-v8-body.html and index.html together, keeping stable <video> source media at max-width:680px, autoplay/muted/loop/playsinline, static poster and reduced-motion fallback.
- Run node scripts/build-hub.mjs --check and relevant Node tests. Check asset include/exclude rules (.assetsignore and .gitignore) to ensure exactly two desired MP4s are published, not old attempts. Dry-run first; inspect paths and byte counts.
- Capture original Worker deployment ID before deployment. Never deploy a stale main branch. Use the exact deployed change-set and minimum asset delta.
- After authorized deploy: hash compare live MP4s, verify HTTP 200 and content-type video/mp4; inspect homepage and ICSI both desktop/mobile, video readyState, currentSrc, visual crop, navigation/avatar, CTA, 5 topic cards, 5 stages, 4 calculators, Journal.
- Commit release evidence and rollback version; keep Git branch clean. Distinguish build PASS, browser PASS and real authenticated SSO E2E.

## Emergency rollback

If new homepage/video fails, confirm active Worker ID before reverting. Use the previous verified Cloudflare deployment ID or targeted asset rollback, never overwrite newer Account/Passport/Journal changes with an old worktree.

## No private assets in the central skills repository

This central repo is public. Never commit videos, screenshots containing people or patients, API keys, WorkOS accounts, uploader identity data, local usernames, private paths, source material from third parties, or a third-party source that lacks redistribution rights. Publish only text, scripts, parameter manifests and hashes.
