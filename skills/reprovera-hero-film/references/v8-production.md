# ReproVera V8: measured production film settings

Source of truth: inspected, original scripts
- design-previews/hero-story-20261117/v8/render-v8.py and render-v8-mobile.py
- design-previews/hero-story-20261117/v8/SOURCES-V8.json and STATUS-V8.md
- design-previews/hero-story-20261117/v8-icsi-upload-preview/render-upload-v8.py and RENDER-MANIFEST.json
- current production assets in the ReproVera release worktree and live https://reprovera.com/

These scripts represent **two distinct revisions**. The first V8 private preview used a different third-party ICSI clip; the approved **production V8** replaces scene 04 with the owner-provided and explicitly authorized clip. Do not restore the obsolete ICSI clip by re-running the original desktop script without replacing scene 04.

## Film and composition

| Element | Production-approved V8 |
| --- | --- |
| Number of scenes | 7, preserved in order |
| Frame rate | 25 fps constant |
| Audio | none, intentional |
| Transition | xfade=transition=fade, **1.12 seconds**, between every adjacent scene |
| Nominal calculated length | 35.80 - 6 × 1.12 = **29.08 seconds** |
| Measured MP4 duration | **29.12 seconds** from frame rounding at 25 fps |
| Desktop | 1280 × 720, H.264 libx264, CRF **21**, preset **medium**, pix_fmt yuv420p, faststart |
| Mobile | 540 × 960, H.264 libx264, CRF **23**, preset **medium**, pix_fmt yuv420p, faststart |
| Original private full-film encodes (not current production) | Desktop CRF 20; mobile CRF 22 |
| Prepared source cuts | Most generated H.264 CRF 19, preset veryfast, 25 fps, with same warm-neutral film grade |
| Crop mobile from 1280 × 720 | crop=405:720:x:0, scale=540:960:flags=bicubic, setsar=1, fps=25, yuv420p |
| Prepared mobile cut settings | CRF 22, preset veryfast, fps=25 |
| Approved ICSI segment preparation | 6.2s, fps=25, tpad=stop_mode=clone:stop_duration=0.10, trim=duration=6.2, setpts=PTS-STARTPTS, CRF18; mobile crop x=170, CRF21 |

### Approved shot breakdown

| # | Scene | Output seconds | Original prepared mobile crop x | Provenance |
| --- | --- | ---: | ---: | --- |
| 01 | Scientist at laboratory microscope | 4.6 | 585 | Pexels 4114800; starts 4.2s in stock, slow 1.09 |
| 02 | IVF laboratory micromanipulator | 4.4 | 440 | Pexels 7705313; starts 3.0s, slow 1.09 |
| 03 | Embryologist hands + lab dish | 3.9 | 540 | Pexels 7705474; starts 1.0s, slow 1.09 |
| 04 | **Real ICSI injection, owner-supplied** | **6.2** | **170 (approved final)** | Owner-approved source clip, processed 1280×720; **not** the original private shot-04 |
| 05 | Embryo 4-cell to blastocyst | 7.6 | 433 | Iwata et al. 2014 supplementary microscopy, CC BY 4.0; 70.754 s compressed to 7.6 s |
| 06 | True 2D obstetric ultrasound | 3.8 | 435 | Pexels 3099938; starts 9.2s, slow 1.09 |
| 07 | Newborn feet | 5.3 | 356 | Pexels 29853744; starts 1.1s, slow 1.13 |

Desktop scene 04 prepared source is the processed 6.2-second approved clip; raw uploaded 14.3s original was 480×360 at ~30fps, and the user-approved intermediate was cropped to 1280×720, without creating true new image detail. Do not describe it as 720p source resolution.

Approved production output SHA-256:

    hero desktop: b60584984d2f8bb083773f237c110d91f3d84827ccfebe9308b9c9340770e302
    hero mobile:  bd494ce0da3d33b501227d3c96f87f991cc7971fd9b849a4377da178ef227034

The known production asset names are:
- assets/video/reprovera-hero-v8-icsi-upload-desktop.mp4
- assets/video/reprovera-hero-v8-icsi-upload-mobile.mp4

The SHA-256 values correspond to *the last approved content*, not a guarantee that another FFmpeg version re-encodes to an identical byte stream. Compare visuals and metadata and document hash changes on a deliberate re-render.

## Exact FFmpeg colour grade from render-v8.py

For standard source shots:

    scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,setsar=1,
    eq=contrast=0.945:brightness=0.009:gamma=1.026:saturation=0.83,
    colorbalance=rs=0.016:gs=0.004:bs=-0.013:rm=0.012:gm=0.002:bm=-0.011:rh=0.008:gh=0.005:bh=-0.012,
    curves=all='0/0.018 0.17/0.193 0.50/0.515 0.82/0.835 1/0.982',
    split=2[crisp][diffuse];[diffuse]gblur=sigma=5.5[glow];
    [crisp][glow]blend=all_expr='A*0.935+B*0.065',fps=25,format=yuv420p

For medical scenes (ICSI, embryo, ultrasound) substitute saturation=0.71. This gives an optical diffusion layer weighted **6.5%** over **93.5%** unblurred pixels; do not use an opaque blur over the image. Preserve original clinical detail, true embryo development, and recognizable ultrasound.

Prepared original shots already received this grade, so never apply it to them a second time. The later owner-provided ICSI intermediate was already manually graded; in the final production montage it was treated as an approved prepared cut.

For ordinary shots, the pre-grade speed transform is setpts=(PTS-STARTPTS)*1.09 (newborn feet 1.13). For the embryo time-lapse, use setpts=(PTS-STARTPTS)*(7.6/70.754) before the grade. This deliberately *accelerates* the scientific sequence.

## Crossfade offsets (seconds)

- 01→02: 3.480
- 02→03: 6.760
- 03→04: 9.540
- 04→05: 14.620
- 05→06: 21.100
- 06→07: 23.780

Use repeated xfade with input indices and offsets; calculate rather than hard-code when durations change.

## Web player (current production)

The video is a decorative, silent, full-width background of a cinematic homepage; the copy and CTA are in normal HTML overlay, **not burnt into the video**.

    <video class="home-hero__film" autoplay muted loop playsinline preload="metadata"
           poster="/assets/img/reprovera-v8-hero-poster.webp" disablepictureinpicture>
      <source media="(max-width: 680px)" src="/assets/video/reprovera-hero-v8-icsi-upload-mobile.mp4" type="video/mp4">
      <source src="/assets/video/reprovera-hero-v8-icsi-upload-desktop.mp4" type="video/mp4">
    </video>

CSS in assets/home-hero-v8.css:
- desktop object-fit: cover; image filter saturate(.86) contrast(.965) brightness(.94);
- mobile filter saturate(.88) contrast(.96) brightness(.91);
- multi-stop dark overlay ensures white text remains legible;
- media query prefers-reduced-motion: reduce sets the video display to none and shows a real poster;
- navigation changes from transparent to frosted light on scroll using assets/home-header-v8.css and home-header-v8.mjs.

Source of HTML is src/site/homepage-v8-body.html via src/site/pages.mjs. Editing only index.html is **not durable**: the generator can later overwrite it. Update canonical source and generated output together; verify with node scripts/build-hub.mjs --check.

## Editorial and legal invariants

- No staged patient-positive-test reactions, family portraits, pregnancy belly or pregnancy success guarantee. Keep clinic/lab competence in the opening and anonymous baby feet at the end.
- No fake AI-generated clinical microinjection; do not replace moving ICSI with a zooming photograph.
- Public science time-lapse attribution: K. Iwata et al., Analysis of compaction initiation in human embryos by using time-lapse cinematography (2014), DOI 10.1007/s10815-014-0195-2, CC BY 4.0, plus changes. As of the validated ReproVera deployment, credit is in the Metodika page under #licence-embryo-video, **not on the homepage**.
- Other raw footage may be Pexels licensed; do not imply stock people are actual clinic patients.
- Preserve exact provenance and hashes in the render report, not in marketing copy.

## Version provenance

Initial film script rendered a private preview with a different, **not-cleared ICSI** source. Later owner provided and explicitly authorized its own ICSI clip. Production version verified 18–19 Nov 2026 is the later variant with the two hashes above. A reference path or old note containing "LICENSE HOLD" is historical and must not override the later source-specific authorization, but does not grant rights to unrelated content. Every *new* substituted source requires its own verified rights decision.
