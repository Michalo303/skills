#!/usr/bin/env python3
"""Deterministic, non-deploying ReproVera hero film renderer.

No third-party Python packages. Requires FFmpeg and ffprobe on PATH.
The input manifest contains paths to user-held footage; no video ships with this skill.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys

DEFAULT_DESKTOP = {"width": 1280, "height": 720, "crf": 21}
DEFAULT_MOBILE = {"width": 540, "height": 960, "crf": 23}
ALLOWED_RIGHTS = {"owner-approved", "licensed", "cc-by", "pending"}
ALLOWED_KINDS = {"prepared", "raw", "time-lapse"}


def die(message: str) -> None:
    raise ValueError(message)


def run(command: list[str], dry_run: bool = False) -> None:
    if dry_run:
        print("DRY RUN:", json.dumps(command, ensure_ascii=False))
    else:
        subprocess.run(command, check=True)


def probe(path: Path) -> dict:
    raw = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration,size:stream=codec_name,codec_type,width,height,r_frame_rate",
        "-of", "json", str(path)
    ], text=True)
    data = json.loads(raw)
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    if not video:
        die(f"No video stream: {path}")
    return {
        "duration": float(data["format"]["duration"]),
        "size": int(data["format"].get("size", 0)),
        "width": int(video["width"]),
        "height": int(video["height"]),
        "fps": video.get("r_frame_rate"),
        "codec": video.get("codec_name")
    }


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def location(value: str, config_dir: Path, source_root: Path | None) -> Path:
    # Resolves relative paths against --source-root when present, else config directory.
    expanded = os.path.expandvars(os.path.expanduser(value))
    p = Path(expanded)
    return p.resolve() if p.is_absolute() else ((source_root or config_dir) / p).resolve()


def scene_inputs(scene: dict, config_dir: Path, source_root: Path | None) -> dict[str, Path]:
    if scene["kind"] == "prepared":
        names = ["prepared_desktop", "prepared_mobile"]
    else:
        names = ["source"]
    return {key: location(scene[key], config_dir, source_root) for key in names if scene.get(key)}


def film_filter(width: int, height: int, fps: int, medical: bool) -> str:
    # Exact V8 FFmpeg grade; this is a *filtergraph*, not a LUT.
    sat = "0.71" if medical else "0.83"
    return (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},setsar=1,"
        f"eq=contrast=0.945:brightness=0.009:gamma=1.026:saturation={sat},"
        "colorbalance=rs=0.016:gs=0.004:bs=-0.013:rm=0.012:gm=0.002:bm=-0.011:"
        "rh=0.008:gh=0.005:bh=-0.012,"
        "curves=all='0/0.018 0.17/0.193 0.50/0.515 0.82/0.835 1/0.982',"
        "split=2[crisp][diffuse];"
        "[diffuse]gblur=sigma=5.5[glow];"
        "[crisp][glow]blend=all_expr='A*0.935+B*0.065',"
        f"fps={fps},format=yuv420p"
    )


def validate(config: dict, config_dir: Path, source_root: Path | None, publish: bool) -> dict:
    if config.get("schema_version") != 1:
        die("schema_version must be 1")
    fps = int(config.get("fps", 25))
    fade = float(config.get("fade_seconds", 1.12))
    if not 1 <= fps <= 60 or not 0.05 <= fade <= 3.0:
        die("Invalid fps or fade_seconds")
    scenes = config.get("scenes")
    if not isinstance(scenes, list) or len(scenes) < 2 or len(scenes) > 20:
        die("Expected 2–20 scenes")
    sizes = {mode: dict(config.get(mode, defaults)) for mode, defaults in
             [("desktop", DEFAULT_DESKTOP), ("mobile", DEFAULT_MOBILE)]}
    for label, size in sizes.items():
        for key in ("width", "height", "crf"):
            size[key] = int(size[key])
        if size["width"] % 2 or size["height"] % 2:
            die(f"{label} dimensions must be even for yuv420p")
        if not 16 <= size["width"] <= 3840 or not 16 <= size["height"] <= 3840:
            die(f"{label} dimensions out of range")
        if not 0 <= size["crf"] <= 40:
            die(f"{label} CRF out of range")
    expected = sum(float(scene["duration"]) for scene in scenes) - fade * (len(scenes) - 1)
    if expected <= 0:
        die("Impossible montage timeline")
    resolved = []
    ids = set()
    for i, scene in enumerate(scenes):
        name = str(scene.get("id", ""))
        if not name or name in ids:
            die(f"Missing or duplicate scene id at {i}")
        ids.add(name)
        if scene.get("kind") not in ALLOWED_KINDS:
            die(f"Scene {name}: invalid kind")
        duration = float(scene.get("duration", 0))
        if not math.isfinite(duration) or duration <= fade + 0.1:
            die(f"Scene {name}: duration must exceed fade + 0.1s")
        rights = scene.get("rights", {})
        if rights.get("status") not in ALLOWED_RIGHTS:
            die(f"Scene {name}: rights.status required")
        if publish and rights.get("status") == "pending":
            die(f"Scene {name}: rights not cleared for public use")
        if publish and rights.get("status") == "cc-by" and not rights.get("attribution"):
            die(f"Scene {name}: CC BY attribution missing")
        if scene["kind"] in ("raw", "time-lapse"):
            if not scene.get("source"):
                die(f"Scene {name}: source required")
            if scene["kind"] == "time-lapse" and float(scene.get("source_duration", 0)) <= 0:
                die(f"Scene {name}: source_duration required")
            if scene["kind"] == "raw" and float(scene.get("speed", 1.0)) <= 0:
                die(f"Scene {name}: invalid speed")
        else:
            if not scene.get("prepared_desktop"):
                die(f"Scene {name}: prepared_desktop required")
        paths = scene_inputs(scene, config_dir, source_root)
        for key, path in paths.items():
            if not path.is_file():
                die(f"Scene {name}: missing {key}: {path}")
        source_hash = scene.get("source_sha256")
        if source_hash:
            key = "prepared_desktop" if scene["kind"] == "prepared" else "source"
            actual = sha256(paths[key])
            if actual.lower() != str(source_hash).lower():
                die(f"Scene {name}: SHA-256 source mismatch (refuse silent substitution)")
        if scene["kind"] == "prepared":
            if scene.get("mobile_sha256") and "prepared_mobile" not in paths:
                die(f"Scene {name}: mobile_sha256 supplied but mobile cut is missing")
            if scene.get("mobile_sha256"):
                actual = sha256(paths["prepared_mobile"])
                if actual.lower() != str(scene["mobile_sha256"]).lower():
                    die(f"Scene {name}: mobile SHA-256 mismatch (refuse silent substitution)")
            for mode, key in (("desktop", "prepared_desktop"), ("mobile", "prepared_mobile")):
                if key in paths:
                    meta = probe(paths[key])
                    size = sizes[mode]
                    if (meta["width"], meta["height"]) != (size["width"], size["height"]):
                        die(f"Scene {name}: prepared {mode} size mismatch")
                    if meta["duration"] < duration - (1 / fps) - 0.001:
                        die(f"Scene {name}: prepared {mode} clip too short")
                    numerator, denominator = (int(z) for z in meta["fps"].split("/"))
                    if abs(numerator / denominator - fps) > 0.01:
                        die(f"Scene {name}: prepared {mode} fps mismatch")
        resolved.append({"scene": scene, "paths": paths})
    return {"fps": fps, "fade": fade, "sizes": sizes, "resolved": resolved,
            "expected_duration": expected, "publish": publish}


def prepare(config: dict, plan: dict, config_dir: Path, source_root: Path | None,
            work: Path) -> dict[str, list[Path]]:
    paths = {"desktop": [], "mobile": []}
    fps = plan["fps"]
    for number, entry in enumerate(plan["resolved"], start=1):
        scene = entry["scene"]
        src = entry["paths"]
        duration = float(scene["duration"])
        desktop = plan["sizes"]["desktop"]
        mobile = plan["sizes"]["mobile"]
        if scene["kind"] == "prepared":
            desk_file = src["prepared_desktop"]
        else:
            desk_file = work / f"shot-{number:02d}-desktop.mp4"
            pre = [ "ffmpeg", "-hide_banner", "-loglevel", "error", "-y" ]
            if scene["kind"] == "raw":
                pre += ["-ss", str(float(scene.get("start", 0)))]
                speed = float(scene.get("speed", 1.0))
                speed_filter = f"setpts=(PTS-STARTPTS)*{speed:.4f},"
            else:
                speed = duration / float(scene["source_duration"])
                speed_filter = f"setpts=(PTS-STARTPTS)*{speed:.10f},"
            filters = speed_filter + film_filter(desktop["width"], desktop["height"], fps,
                                                 bool(scene.get("medical", False)))
            command = pre + ["-i", str(src["source"]), "-an", "-vf", filters,
                             "-t", str(duration), "-c:v", "libx264",
                             "-preset", "veryfast", "-crf", "19",
                             "-pix_fmt", "yuv420p", "-r", str(fps),
                             "-movflags", "+faststart", str(desk_file)]
            run(command)
        paths["desktop"].append(desk_file)
        if "prepared_mobile" in src:
            mobile_file = src["prepared_mobile"]
        else:
            mobile_file = work / f"shot-{number:02d}-mobile.mp4"
            crop_width = round(desktop["height"] * mobile["width"] / mobile["height"])
            x = int(scene.get("mobile_crop_x", (desktop["width"] - crop_width) / 2))
            if not 0 <= x <= desktop["width"] - crop_width:
                die(f"Scene {scene['id']}: invalid mobile_crop_x {x}")
            filt = (f"crop={crop_width}:{desktop['height']}:{x}:0,"
                    f"scale={mobile['width']}:{mobile['height']}:flags=bicubic,"
                    f"setsar=1,fps={fps},format=yuv420p")
            run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                 "-i", str(desk_file), "-an", "-vf", filt,
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                 "-r", str(fps), "-pix_fmt", "yuv420p", str(mobile_file)])
        paths["mobile"].append(mobile_file)
    return paths


def merge(paths: list[Path], config: dict, plan: dict, output: Path, mode: str) -> dict:
    duration = float(plan["resolved"][0]["scene"]["duration"])
    last = "0:v"
    fades = []
    for index, item in enumerate(plan["resolved"][1:], start=1):
        label = f"transition{index}"
        fades.append(f"[{last}][{index}:v]xfade=transition=fade:"
                     f"duration={plan['fade']:.3f}:offset={duration-plan['fade']:.3f}"
                     f"[{label}]")
        last = label
        duration += float(item["scene"]["duration"]) - plan["fade"]
    size = plan["sizes"][mode]
    inputs = sum((["-i", str(file)] for file in paths), [])
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"] + inputs +
        ["-filter_complex", ";".join(fades), "-map", f"[{last}]",
         "-an", "-c:v", "libx264", "-preset", "medium",
         "-crf", str(size["crf"]), "-pix_fmt", "yuv420p",
         "-r", str(plan["fps"]), "-movflags", "+faststart", str(output)])
    result = probe(output)
    if (result["width"], result["height"]) != (size["width"], size["height"]):
        die(f"{mode} output dimension mismatch")
    if abs(result["duration"] - plan["expected_duration"]) > 0.13:
        die(f"{mode} output timeline drift: {result['duration']} vs {plan['expected_duration']}")
    return {"path": str(output), "sha256": sha256(output), **result}


def render(config_path: Path, source_root: Path | None, out: Path, publish: bool,
           overwrite: bool) -> dict:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    plan = validate(config, config_path.parent, source_root, publish)
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        die("ffmpeg and ffprobe must be installed on PATH")
    outputs = [out / "hero-desktop.mp4", out / "hero-mobile.mp4",
               out / "hero-render-report.json"]
    if not overwrite and any(p.exists() for p in outputs):
        die("Output exists. Choose a fresh directory; --overwrite is explicit.")
    out.mkdir(parents=True, exist_ok=True)
    for entry in plan["resolved"]:
        for source in entry["paths"].values():
            if source in outputs:
                die("Output path conflicts with an input source; refusing overwrite")
    work = out / "work"
    work.mkdir(exist_ok=True)
    prepared = prepare(config, plan, config_path.parent, source_root, work)
    rendered = {
        mode: merge(prepared[mode], config, plan, out / f"hero-{mode}.mp4", mode)
        for mode in ("desktop", "mobile")
    }
    report = {
        "config": str(config_path), "fade_seconds": plan["fade"],
        "fps": plan["fps"], "expected_duration": plan["expected_duration"],
        "mode": "public-candidate" if publish else "private-preview",
        "scenes": [{"id": item["scene"]["id"], "duration": item["scene"]["duration"],
                    "kind": item["scene"]["kind"], "rights": item["scene"]["rights"],
                    "inputs": {k: {"path": str(v), "sha256": sha256(v)}
                               for k, v in item["paths"].items()}}
                   for item in plan["resolved"]],
        "outputs": rendered, "deployment": "NOT DEPLOYED: approval and independent release gate required"
    }
    outputs[-1].write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--source-root", type=Path, help="Source directory for relative manifest paths")
    parser.add_argument("--out-dir", type=Path, help="Required only with --render")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Validate sources, SHA and rights; no writes")
    group.add_argument("--render", action="store_true", help="Render new private desktop/mobile candidates")
    parser.add_argument("--public-candidate", action="store_true",
                        help="Fail unless all footage rights are cleared; NEVER deploys")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        cfg = args.config.resolve()
        if not cfg.is_file():
            die(f"Config not found: {cfg}")
        source_root = args.source_root.resolve() if args.source_root else None
        if args.check:
            data = validate(json.loads(cfg.read_text(encoding="utf8")), cfg.parent,
                            source_root, args.public_candidate)
            print(json.dumps({"status": "PASS", "scenes": len(data["resolved"]),
                              "expected_duration": data["expected_duration"],
                              "public_candidate": data["publish"]}, indent=2))
        else:
            if not args.out_dir:
                die("--out-dir required with --render")
            report = render(cfg, source_root, args.out_dir.resolve(),
                            args.public_candidate, args.overwrite)
            print(json.dumps(report["outputs"], indent=2))
        return 0
    except (ValueError, FileNotFoundError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
