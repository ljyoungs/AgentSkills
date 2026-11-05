"""Behavior checks with synthetic media; no private pictures or online generation."""

import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image, ImageDraw

PACKAGE = (
    Path(__file__).resolve().parents[1] / "skills/content-creation/photo-beat-video"
)
sys.path.insert(0, str(PACKAGE / "scripts"))
import music_cache as music  # noqa: E402
import photo_beat as video  # noqa: E402


class Response:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        return None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def iter_content(self, size):
        for pos in range(0, len(self.content), size):
            yield self.content[pos : pos + size]


class Source:
    def __init__(self, content):
        self.content = content
        self.requests = 0

    def get(self, *args, **kwargs):
        self.requests += 1
        if self.content is None:
            raise AssertionError(
                "A valid cached soundtrack must not require network access"
            )
        return Response(self.content)


class PhotoVideoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = tempfile.TemporaryDirectory(prefix="photo-beat-tests-")
        cls.root = Path(cls.workspace.name)
        cls.photos = []
        for i, color in enumerate(
            [(120, 65, 45), (40, 100, 150), (95, 120, 55), (100, 65, 125)]
        ):
            path = cls.root / f"original-{i}.png"
            image = Image.new("RGB", (192, 320), color)
            draw = ImageDraw.Draw(image)
            draw.rectangle((8, 8, 183, 311), outline="white", width=3)
            draw.ellipse((45, 80, 145, 210), fill=(210, 170, 120))
            image.save(path)
            cls.photos.append(path)
        cls.motion = cls.root / "synthetic-motion.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-n",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=size=192x320:rate=24",
                "-t",
                "3",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(cls.motion),
            ],
            check=True,
        )
        cls.sound = cls.root / "synthetic-sound.mp3"
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-n",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=330:sample_rate=48000",
                "-t",
                "16",
                "-c:a",
                "libmp3lame",
                str(cls.sound),
            ],
            check=True,
        )
        cls.template = {
            "music": {
                "source_page": "https://example.test/original",
                "download_url": "https://example.test/sound.mp3",
                "source_sha256": music.sha(cls.sound),
                "duration_seconds": 16.032,
            },
            "beat_times": [
                0.2,
                0.8,
                1.4,
                2.0,
                2.6,
                3.2,
                4.0,
                5.0,
                6.0,
                7.0,
                8.0,
                9.0,
                10.0,
                11.0,
                12.0,
            ],
        }

    @classmethod
    def tearDownClass(cls):
        cls.workspace.cleanup()

    def cache(self, suffix=""):
        return self.root / (self._testMethodName + suffix)

    def audio(self):
        return music.ensure_music(
            self.template, self.cache("-music"), Source(self.sound.read_bytes())
        )

    def plan(self, **kwargs):
        return video.create_plan(
            self.photos[:3],
            template=self.template,
            width=180,
            height=320,
            fps=12,
            **kwargs,
        )

    def frame(self, path, number, width=180, height=320):
        result = subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-i",
                str(path),
                "-vf",
                f"select=eq(n\\,{number})",
                "-frames:v",
                "1",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "rgb24",
                "-",
            ],
            capture_output=True,
            check=True,
        )
        return (
            np.frombuffer(result.stdout, dtype=np.uint8)
            .reshape(height, width, 3)
            .astype(float)
        )

    def test_fixed_music_download_then_offline_cache(self):
        source = Source(self.sound.read_bytes())
        first = music.ensure_music(self.template, self.cache(), source)
        second = music.ensure_music(self.template, self.cache(), Source(None))
        self.assertEqual(source.requests, 1)
        self.assertEqual(first["sha256"], second["sha256"])
        self.assertTrue(second["cache_reused"])
        self.assertFalse(second["music_speed_pitch_gain_fades_changed"])

    def test_changed_source_never_becomes_the_soundtrack(self):
        with self.assertRaisesRegex(RuntimeError, "SHA256 mismatch"):
            music.ensure_music(self.template, self.cache(), Source(b"a different song"))
        self.assertEqual(list(self.cache().glob("*.mp3")), [])
        self.assertEqual(list(self.cache().glob("*.m4a")), [])

    def test_tampered_cache_stops_without_overwriting_it(self):
        info = self.audio()
        path = Path(info["path"])
        path.write_bytes(path.read_bytes() + b"changed")
        changed = music.sha(path)
        with self.assertRaisesRegex(RuntimeError, "cannot be verified"):
            music.ensure_music(self.template, self.cache("-music"), Source(None))
        self.assertEqual(music.sha(path), changed)

    def test_full_template_needs_real_motion_and_valid_source_interval(self):
        with self.assertRaisesRegex(ValueError, "real motion"):
            self.plan(mode="sweet-cool", styled=self.photos[:3])
        with self.assertRaisesRegex(ValueError, "exceeds"):
            self.plan(
                mode="sweet-cool",
                styled=self.photos[:3],
                motion=self.motion,
                motion_start=2.5,
                motion_duration=1,
            )

    def test_photo_plan_retains_inputs_and_is_frame_continuous(self):
        plan = video.create_plan(
            self.photos,
            template=self.template,
            width=180,
            height=320,
            fps=12,
            duration=4,
        )
        self.assertEqual(
            [s["path"] for s in plan["shots"]], [str(p.resolve()) for p in self.photos]
        )
        self.assertEqual(plan["frames"], 48)
        for previous, following in zip(plan["shots"], plan["shots"][1:]):
            self.assertEqual(previous["end_frame_exclusive"], following["start_frame"])
        self.assertEqual(plan["omitted_opening_photos"], [])

    def test_dense_photo_inputs_fit_the_available_frames(self):
        plan = video.create_plan(
            [self.photos[0]] * 15,
            template=self.template,
            width=180,
            height=320,
            fps=12,
            duration=2,
        )
        self.assertEqual(plan["frames"], 24)
        self.assertEqual(len(plan["shots"]), 15)
        self.assertTrue(all(shot["frames"] >= 1 for shot in plan["shots"]))

    def test_photo_render_preserves_original_and_exact_cached_music_packets(self):
        before = [music.sha(p) for p in self.photos]
        plan = video.create_plan(
            [self.photos[0]],
            template=self.template,
            width=180,
            height=320,
            fps=10,
            duration=1,
        )
        out = self.cache("-render")
        with contextlib.redirect_stdout(io.StringIO()):
            result = video.render(plan, self.audio(), out)
        self.assertTrue(result["technical_pass"])
        self.assertTrue(result["audio_cache_prefix_packets_match"])
        self.assertEqual(before, [music.sha(p) for p in self.photos])
        # The encoded beat flash is measurably brighter and retains the colored photo.
        flash = self.frame(out / "result.mp4", 2)
        rest = self.frame(out / "result.mp4", 7)
        self.assertGreater(flash.mean() - rest.mean(), 4)
        self.assertGreater(np.abs(flash[:, :, 0] - flash[:, :, 2]).mean(), 15)
        existing = music.sha(out / "result.mp4")
        with self.assertRaises(FileExistsError):
            video.render(plan, self.audio(), out)
        self.assertEqual(music.sha(out / "result.mp4"), existing)

    def test_full_edit_freezes_the_actual_last_motion_frame(self):
        # No effect pulses at the transition, so compare actual encoded content.
        template = {**self.template, "beat_times": []}
        plan = video.create_plan(
            self.photos,
            styled=self.photos[:3],
            motion=self.motion,
            mode="sweet-cool",
            template=template,
            width=180,
            height=320,
            fps=12,
            motion_start=0.5,
            motion_duration=1,
            speed=0.8,
        )
        self.assertEqual(len(plan["omitted_opening_photos"]), 1)
        out = self.cache("-render")
        with contextlib.redirect_stdout(io.StringIO()):
            result = video.render(plan, self.audio(), out)
        self.assertTrue(result["technical_pass"])
        motion, freeze = plan["shots"][-2:]
        selected_last = self.frame(out / "selected-motion.mp4", motion["frames"] - 1)
        actual_freeze = self.frame(out / "result.mp4", freeze["start_frame"])
        self.assertLess(np.abs(selected_last - actual_freeze).mean(), 4)
        selected_first = self.frame(out / "selected-motion.mp4", 0)
        self.assertGreater(np.abs(selected_first - actual_freeze).mean(), 5)
        qa = json.loads((out / "qa/qa.json").read_text(encoding="utf-8"))
        self.assertEqual(qa["user_aesthetic_approval"], "pending")


if __name__ == "__main__":
    unittest.main()
