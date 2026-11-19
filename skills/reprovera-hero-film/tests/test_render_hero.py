#!/usr/bin/env python3
"""Smoke and regression tests for the portable film renderer; no real footage."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

RENDERER = Path(__file__).resolve().parents[1] / "scripts" / "render_hero.py"
spec = importlib.util.spec_from_file_location("reprovera_hero_renderer", RENDERER)
renderer = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(renderer)


class RendererTests(unittest.TestCase):
    def test_original_grade_parameters(self):
        for medical, saturation in [(False, "0.83"), (True, "0.71")]:
            text = renderer.film_filter(1280, 720, 25, medical)
            self.assertIn("eq=contrast=0.945:brightness=0.009:gamma=1.026", text)
            self.assertIn(f"saturation={saturation}", text)
            self.assertIn("gblur=sigma=5.5", text)
            self.assertIn("A*0.935+B*0.065", text)
            self.assertIn("curves=all=", text)
            self.assertIn("fps=25,format=yuv420p", text)

    def test_pending_rights_are_blocked(self):
        with tempfile.TemporaryDirectory() as folder:
            cfg = {
                "schema_version": 1, "fps": 10, "fade_seconds": 0.5,
                "scenes": [
                    {"id": "01", "kind": "prepared", "duration": 2.0,
                     "prepared_desktop": "not-present.mp4",
                     "rights": {"status": "pending"}},
                    {"id": "02", "kind": "prepared", "duration": 2.0,
                     "prepared_desktop": "not-present.mp4",
                     "rights": {"status": "licensed"}}
                ]
            }
            with self.assertRaisesRegex(ValueError, "rights not cleared"):
                renderer.validate(cfg, Path(folder), None, True)

    def test_missing_source_fails_closed(self):
        cfg = {
            "schema_version": 1, "fps": 10, "fade_seconds": .5,
            "scenes": [
                {"id": str(i), "kind": "raw", "duration": 2.0,
                 "source": "absent.mp4", "rights": {"status": "licensed"}}
                for i in range(2)
            ]
        }
        with self.assertRaisesRegex(ValueError, "missing source"):
            renderer.validate(cfg, Path.cwd(), None, False)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "ffmpeg and ffprobe required for synthetic render")
    def test_synthetic_three_scene_render_and_mobile_crop(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            width, height, fps = 160, 90, 10
            for i, color in enumerate(["red", "blue", "green"], start=1):
                subprocess.run([
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", f"color=c={color}:s=160x90:r=10:d=3",
                    "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    str(root / f"s{i}.mp4")
                ], check=True)
            subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "color=c=red:s=90x160:r=10:d=3",
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                str(root / "s1-mobile.mp4")
            ], check=True)
            cfg = {
                "schema_version": 1, "fps": fps, "fade_seconds": 0.5,
                "desktop": {"width": width, "height": height, "crf": 31},
                "mobile": {"width": 90, "height": 160, "crf": 33},
                "scenes": [
                    {"id": "01", "kind": "prepared", "duration": 2.2,
                     "prepared_desktop": "s1.mp4", "prepared_mobile": "s1-mobile.mp4",
                     "rights": {"status": "licensed"}},
                    {"id": "02", "kind": "raw", "duration": 2.2, "source": "s2.mp4",
                     "start": 0, "speed": 1.05, "mobile_crop_x": 50,
                     "rights": {"status": "owner-approved"}},
                    {"id": "03", "kind": "time-lapse", "duration": 2.2,
                     "source_duration": 3.0, "source": "s3.mp4",
                     "medical": True, "mobile_crop_x": 50,
                     "rights": {"status": "cc-by", "attribution": "Test synthetic clip"}},
                ]
            }
            config = root / "input.json"
            config.write_text(json.dumps(cfg), encoding="utf8")
            # Provenance must block an intentional or accidental source substitution.
            wrong = json.loads(json.dumps(cfg))
            wrong["scenes"][0]["source_sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "SHA-256 source mismatch"):
                renderer.validate(wrong, root, None, True)
            output = root / "output"
            report = renderer.render(config, None, output, True, False)
            self.assertEqual(report["mode"], "public-candidate")
            for mode, expected in [("desktop", (160, 90)), ("mobile", (90, 160))]:
                meta = report["outputs"][mode]
                self.assertEqual((meta["width"], meta["height"]), expected)
                self.assertEqual(meta["codec"], "h264")
                self.assertLess(abs(meta["duration"] - 5.6), .13)
                self.assertEqual(len(meta["sha256"]), 64)
            self.assertEqual(len(report["scenes"]), 3)
            with self.assertRaisesRegex(ValueError, "Output exists"):
                renderer.render(config, None, output, True, False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
