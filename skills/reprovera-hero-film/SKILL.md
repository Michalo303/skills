---
name: reprovera-hero-film
description: Use when replacing, re-editing, grading, exporting or safely releasing the ReproVera homepage cinematic IVF hero video; preserve owner-approved V8 shots, colour palette, transition timing, rights, mobile crop and verified production frontend.
---

# ReproVera homepage hero-film editing

Use this skill **before changing any ReproVera hero video, poster, header overlay, or movie URLs**. The baseline is the owner-approved **production V8 (November 2026)**, not the original private V8 that used a different, third-party ICSI clip.

## Read verified sources and preserve product intent

1. Read [V8 production specification](references/v8-production.md) and inspect the actual scripts, selected clips, FFmpeg/ffprobe metadata, release manifest, and Git status. Never trust a previous chat summary over files.
2. Read [rights and release gates](references/release-safety.md) before a public-facing edit.
3. Locate the current canonical ReproVera source and the latest live deployment; verify whether current production matches that source. Live production outranks an older main branch or stale worktree. Do not overwrite Account, Passport, Clinic, Journal, consent, header/footer, other pages, or uncommitted changes.
4. Work in an isolated preview workspace/branch. Preserve original video by SHA-256 and never render over it.
5. Start from [production V8 manifest](examples/production-v8.json). All footage is **external**, staged by the agent in an isolated source directory. No footage, patient records or private paths ship with this skill.
6. On a single-scene change, retain the other six approved desktop/mobile cut files *byte-identically*. Record the replaced scene's SHA, timing, licence, and per-scene mobile crop.
7. Render **both** desktop and mobile using [render_hero.py](scripts/render_hero.py). Examine sampled frames and real playback in a preview of the site, including desktop, mobile and Firefox; FFmpeg success is not visual QA.
8. Tell the owner exactly what changed, including any removed/replaced shots, altered text and total duration. Obtain explicit approval. A request to edit video is **not** permission to deploy.
9. Only if public deployment is separately authorized, confirm rights and attribution, use the current production-matched frontend, stage the minimum changed assets and compare the complete navigation/header/footer. Capture Git commit, deployment version, exact published SHA-256 and live browser smoke tests. Never present a Git push or dry run as a successful release.

## Reproducing V8 (PowerShell)

Place original V8 prepared cuts in a *new* source directory (do not edit existing working originals):

    staged/graded/shot-01.mp4 ... shot-07.mp4
    staged/mobilecuts/v8-mobile-shot-01.mp4 ... v8-mobile-shot-07.mp4
    staged/cuts/04-user-approved-icsi.mp4
    staged/cuts/04-user-approved-icsi-mobile.mp4

The manifest references those relative names. Scene 04 uses its owner-approved replacement, not the original V8 shot-04. Verify its SHA-256 rather than trusting a matching filename.

    python skills/reprovera-hero-film/scripts/render_hero.py --config skills/reprovera-hero-film/examples/production-v8.json --source-root C:\path\to\staged --check --public-candidate
    python skills/reprovera-hero-film/scripts/render_hero.py --config skills/reprovera-hero-film/examples/production-v8.json --source-root C:\path\to\staged --out-dir C:\path\to\new-preview --render --public-candidate
    ffprobe -v error -show_entries format=duration,size:stream=width,height,r_frame_rate -of json C:\path\to\new-preview\hero-desktop.mp4

This script does not download footage or deploy. It rejects missing sources, altered hashes, invalid mobile geometry, uncleared rights in public-candidate mode, and overwriting output unless explicitly authorized. It generates a source manifest and output hashes.

To edit a **raw new shot**, switch its manifest entry from kind="prepared" to kind="raw" with source, start, duration, speed, medical and mobile_crop_x. For actual time-lapse acceleration, use kind="time-lapse" and source_duration. Both apply the exact V8 gentle grading. Do not double-grade files marked prepared. Changing a hash in the manifest is a **documented owner-approved substitution**, never a way to bypass failed provenance.

## Established editorial constraints

- Seven-scene arc: female lab scientist at microscope → IVF micromanipulator → embryologist hands → real moving ICSI → human embryo development → authentic 2D fetal ultrasound → anonymous newborn feet.
- Keep the professional opening and impersonal, hopeful ending. No pregnancy-test reaction, pregnant belly, staged family intimacy, positive-outcome promise, synthetic clinical footage, replacement of moving ICSI with a still, or unapproved additional scenes.
- Soft low-contrast warm-neutral film look inspired by Medivox, not copied Medivox media. Biological microscopy must stay legible.
- Current CC BY scientific microscopy needs attribution with the author, DOI, license, and description of modifications. The credit belongs in the public Metodika page, not on the homepage. Other source rights must be verified for the intended use.
- Preserve browser semantics: autoplay muted loop playsinline preload="metadata", mobile source at max-width 680px, fallback poster, reduced-motion still. Do not change authentication or consent to support video.

## Definition of done

Report scene order and changes, exact source paths/hashes and rights, FFmpeg commands and filters, desktop/mobile duration/resolution/codec and final hashes, preview screenshots and browser playback, Git branch/commit where used, **PREVIEW versus PROD**, and every deletion. Retain release and rollback evidence after authorized deployment.
