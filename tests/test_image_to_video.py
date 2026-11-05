"""Offline behavior tests: fake provider, real local media decoding; no remote generations."""

import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock
import requests
from PIL import Image
import sys

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[1]
        / "skills/content-creation/image-to-video/scripts"
    ),
)
import image_to_video as i2v


class Response:
    def __init__(self, data=None, lines=None, content=b"", fail_download=False):
        self.data, self.lines, self.content = data, lines, content
        self.fail_download = fail_download

    def raise_for_status(self):
        return None

    def json(self):
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def iter_lines(self, **kwargs):
        yield from (self.lines or [])

    def iter_content(self, size):
        if self.fail_download:
            yield self.content[:64]
            raise requests.ConnectionError("Simulated interrupted media download")
        for pos in range(0, len(self.content), size):
            yield self.content[pos : pos + size]


class Provider:
    def __init__(
        self,
        content=b"",
        *,
        schema_changed=False,
        remote_error=False,
        unknown_submit=False,
        fail_download=False,
        remote_message=None,
    ):
        self.content = content
        self.schema_changed = schema_changed
        self.remote_error = remote_error
        self.unknown_submit = unknown_submit
        self.fail_download = fail_download
        self.remote_message = remote_message
        self.uploads = self.submits = self.polls = self.downloads = 0

    def get(self, url, **kwargs):
        if url.endswith("/info"):
            names = ["changed"] if self.schema_changed else i2v.PARAMS
            return Response(
                {
                    "named_endpoints": {
                        "/generate_video": {
                            "parameters": [{"parameter_name": n} for n in names]
                        }
                    }
                }
            )
        if "/call/generate_video/" in url:
            self.polls += 1
            if self.remote_error:
                return Response(
                    lines=["event: error", "data: " + json.dumps(self.remote_message)]
                )
            f = {
                "path": "/tmp/generated.mp4",
                "url": i2v.BASE + "/gradio_api/file=/tmp/generated.mp4",
                "meta": {"_type": "gradio.FileData"},
            }
            return Response(
                lines=[
                    "event: heartbeat",
                    "data: null",
                    "event: complete",
                    "data: " + json.dumps([f, 17]),
                ]
            )
        if "/file=" in url:
            self.downloads += 1
            return Response(content=self.content, fail_download=self.fail_download)
        raise AssertionError("Unexpected GET " + url)

    def post(self, url, **kwargs):
        if url.endswith("/upload"):
            self.uploads += 1
            return Response(["/tmp/upload/input.png"])
        if url.endswith("/call/generate_video"):
            self.submits += 1
            if self.unknown_submit:
                raise requests.Timeout("Simulated uncertain POST completion")
            return Response({"event_id": "existing-event-123"})
        raise AssertionError("Unexpected POST " + url)


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="i2v-tests-")
        cls.root = Path(cls.temp.name)
        cls.image = cls.root / "input.png"
        Image.new("RGB", (360, 640), (100, 140, 170)).save(cls.image)
        cls.prompt = cls.root / "prompt.txt"
        cls.prompt.write_text(
            "A small natural subject movement; steady framing.", encoding="utf-8"
        )
        cls.movie = cls.root / "fixture.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-n",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=size=320x192:rate=12",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:sample_rate=48000",
                "-t",
                "1",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-shortest",
                str(cls.movie),
            ],
            check=True,
        )
        cls.data = cls.movie.read_bytes()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def plan(self, audio_mode="mute"):
        return i2v.make_plan(self.image, self.prompt, duration=1, audio_mode=audio_mode)

    def out(self, name):
        return self.root / (name + "-" + self._testMethodName)

    def receipt(self, out):
        return json.loads((out / "receipt.json").read_text(encoding="utf-8"))

    def test_landscape_portrait_square_and_pair_validation(self):
        dims = []
        for w, h in [(360, 640), (640, 360), (512, 512)]:
            p = self.root / ("shape-%s-%s.png" % (w, h))
            Image.new("RGB", (w, h)).save(p)
            plan = i2v.make_plan(p, self.prompt)
            dims.append((plan["width"], plan["height"]))
        self.assertLess(dims[0][0], dims[0][1])
        self.assertGreater(dims[1][0], dims[1][1])
        self.assertEqual(dims[2][0], dims[2][1])
        with self.assertRaises(ValueError):
            i2v.make_plan(self.image, self.prompt, width=1088)

    def test_transparent_image_requires_background_before_upload(self):
        p = self.root / "transparent.png"
        Image.new("RGBA", (320, 320), (255, 0, 0, 0)).save(p)
        with self.assertRaises(ValueError):
            i2v.make_plan(p, self.prompt)

    def test_invalid_wait_cannot_create_remote_task(self):
        p = Provider(self.data)
        with self.assertRaises(ValueError):
            i2v.generate(self.plan(), self.out("wait"), p, wait_seconds=0)
        self.assertEqual((p.uploads, p.submits), (0, 0))

    def test_schema_change_stops_before_any_upload(self):
        p = Provider(schema_changed=True)
        out = self.out("schema")
        with self.assertRaises(i2v.WorkflowError):
            i2v.generate(self.plan(), out, p)
        self.assertEqual((p.uploads, p.submits), (0, 0))
        self.assertEqual(self.receipt(out)["status"], "preparation_failed")

    def test_unknown_submission_is_not_repeated(self):
        p = Provider(unknown_submit=True)
        out = self.out("unknown")
        with self.assertRaises(requests.Timeout):
            i2v.generate(self.plan(), out, p)
        self.assertEqual(self.receipt(out)["status"], "submission_unknown")
        with self.assertRaises(FileExistsError):
            i2v.generate(self.plan(), out, p)
        with self.assertRaises(i2v.WorkflowError):
            i2v.resume(out, p)
        self.assertEqual(p.submits, 1)
        self.assertEqual(p.uploads, 1)

    def test_null_error_preserves_unknown_reason(self):
        p = Provider(remote_error=True)
        out = self.out("null")
        with self.assertRaises(i2v.WorkflowError):
            i2v.generate(self.plan(), out, p)
        r = self.receipt(out)
        self.assertEqual(r["status"], "remote_failed")
        self.assertIsNone(r["remote_error"])
        self.assertFalse(r["failure_reason_known"])
        self.assertEqual(r["failure_category"], "unknown")
        with self.assertRaises(i2v.WorkflowError):
            i2v.resume(out, p)
        self.assertEqual(p.submits, 1)

    def test_quota_failure_keeps_provider_countdown_and_never_resubmits(self):
        message = "You have exceeded your ZeroGPU quota (120s requested vs. -1s left). Try again in 17:54:25."
        p = Provider(remote_error=True, remote_message={"message": message})
        out = self.out("quota")
        with self.assertRaises(i2v.WorkflowError):
            i2v.generate(self.plan(), out, p)
        receipt = self.receipt(out)
        self.assertEqual(receipt["failure_category"], "quota_exhausted")
        self.assertEqual(receipt["provider_retry_after"], "17:54:25")
        self.assertTrue(receipt["failure_reason_known"])
        self.assertIsNone(receipt["automatic_retry_at"])
        self.assertEqual(receipt["auth_mode"], "anonymous")
        with self.assertRaises(i2v.WorkflowError):
            i2v.resume(out, p)
        self.assertEqual((p.uploads, p.submits, p.polls), (1, 1, 1))

    def test_schema_reachable_does_not_imply_account_or_quota_verified(self):
        result = i2v.doctor(Provider())
        self.assertTrue(result["schema_matches"])
        self.assertEqual(result["auth_mode"], "anonymous")
        self.assertFalse(result["quota_verified"])

    def test_embedded_adapter_matches_independently_installable_package(self):
        package = Path(__file__).resolve().parents[1] / "skills/content-creation"
        self.assertEqual(
            (package / "image-to-video/scripts/image_to_video.py").read_bytes(),
            (package / "photo-beat-video/scripts/image_to_video.py").read_bytes(),
        )

    def test_handoff_is_offline_portable_and_preserves_inputs(self):
        out = self.out("handoff")
        before = i2v.sha(self.image)
        with mock.patch.object(
            i2v.requests, "Session", side_effect=AssertionError("No network")
        ):
            result = i2v.handoff(self.plan(), out)
        self.assertFalse(result["generation_submitted"])
        self.assertEqual(result["submissions"], 0)
        self.assertEqual(result["status"], "manual_generation_pending")
        self.assertEqual(i2v.sha(self.image), before)
        manifest = json.loads((out / "handoff.json").read_text(encoding="utf-8"))
        self.assertEqual(i2v.sha(out / manifest["image"]), manifest["image_sha256"])
        self.assertEqual(
            (out / manifest["prompt_file"]).read_text(encoding="utf-8"),
            self.plan()["prompt"],
        )
        self.assertNotIn(str(self.root), json.dumps(manifest))
        with Image.open(out / manifest["image"]) as image:
            self.assertEqual(image.size, (360, 640))
        with self.assertRaises(FileExistsError):
            i2v.handoff(self.plan(), out)

    def test_handoff_rejects_reference_changed_after_planning(self):
        image = self.out("reference").with_suffix(".png")
        Image.new("RGB", (360, 640)).save(image)
        plan = i2v.make_plan(image, self.prompt)
        Image.new("RGB", (360, 640), "red").save(image)
        out = self.out("changed-handoff")
        with self.assertRaises(i2v.WorkflowError):
            i2v.handoff(plan, out)
        self.assertFalse(out.exists())

    def test_handoff_cli_accepts_unicode_paths_and_writes_no_generation_receipt(self):
        out = self.out("中文交接包")
        completed = subprocess.run(
            [
                sys.executable,
                "-X",
                "utf8",
                i2v.__file__,
                "handoff",
                "--image",
                str(self.image),
                "--prompt-file",
                str(self.prompt),
                "--duration",
                "5",
                "--out",
                str(out),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        result = json.loads(completed.stdout)
        self.assertEqual(result["requested_settings"]["duration"], 5)
        self.assertFalse(result["generation_submitted"])
        self.assertTrue((out / "使用说明.txt").is_file())
        self.assertFalse((out / "receipt.json").exists())

    def test_resume_download_never_uploads_or_submits_again(self):
        p = Provider(self.data, fail_download=True)
        out = self.out("resume")
        with self.assertRaises(requests.ConnectionError):
            i2v.generate(self.plan(), out, p)
        self.assertEqual(self.receipt(out)["status"], "download_interrupted")
        self.assertFalse((out / "source.mp4").exists())
        p.fail_download = False
        result = i2v.resume(out, p)
        self.assertEqual(result["status"], "ready")
        self.assertEqual((p.uploads, p.submits, p.polls, p.downloads), (1, 1, 1, 2))
        self.assertEqual(i2v.sha(out / "source.mp4"), i2v.sha(self.movie))
        self.assertFalse(
            json.loads((out / "qa/qa.json").read_text(encoding="utf-8"))[
                "audio_present"
            ]
        )

    def test_requested_model_audio_is_retained_and_prior_output_preserved(self):
        p = Provider(self.data)
        out = self.out("sound")
        result = i2v.generate(self.plan("model"), out, p)
        qa = json.loads((out / "qa/qa.json").read_text(encoding="utf-8"))
        self.assertTrue(qa["audio_present"])
        self.assertTrue(qa["full_decode_pass"])
        self.assertEqual(len(qa["samples"]), 7)
        self.assertGreater(max(qa["sampled_frame_mean_abs_differences"]), 1)
        before = i2v.sha(out / "result.mp4")
        i2v.resume(out, p)
        self.assertEqual(i2v.sha(out / "result.mp4"), before)
        self.assertEqual(p.submits, 1)
        self.assertEqual(result["model_visual_review"], "pending actual inspection")


if __name__ == "__main__":
    with contextlib.redirect_stdout(io.StringIO()):
        unittest.main(verbosity=2)
