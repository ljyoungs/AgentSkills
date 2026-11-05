"""Reusable first-frame I2V with durable receipts and no automatic resubmission."""

from __future__ import annotations
import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.parse import urljoin, urlsplit

import requests
from PIL import Image, ImageOps

BASE = "https://linoyts-ltx-2-3-first-last-frame.hf.space"
SPACE = "https://huggingface.co/spaces/linoyts/LTX-2-3-First-Last-Frame"
PARAMS = [
    "first_image",
    "last_image",
    "input_audio",
    "prompt",
    "duration",
    "enhance_prompt",
    "seed",
    "randomize_seed",
    "height",
    "width",
]


class WorkflowError(RuntimeError):
    pass


def now():
    return datetime.now(timezone(timedelta(hours=8))).isoformat()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def save(path, value):
    path = Path(path)
    temp = path.with_name(path.name + ".writing")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def event(root, stage, **fields):
    value = {"at": now(), "stage": stage, **fields}
    with (Path(root) / "events.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(value, ensure_ascii=False) + "\n")
    print(json.dumps(value, ensure_ascii=False), flush=True)


def update(root, receipt, status, **fields):
    receipt.update(status=status, updated_at=now(), **fields)
    save(Path(root) / "receipt.json", receipt)
    event(root, status)


def make_plan(
    image,
    prompt_file,
    duration=6,
    width=None,
    height=None,
    long_edge=1280,
    seed=17,
    audio_mode="mute",
):
    image, prompt_file = Path(image).resolve(), Path(prompt_file).resolve()
    with Image.open(image) as im:
        if getattr(im, "is_animated", False):
            raise ValueError(
                "Use a chosen static reference frame, not an unreviewed animated image."
            )
        if "A" in im.getbands() and im.getchannel("A").getextrema()[0] < 255:
            raise ValueError(
                "Transparent reference needs an explicitly chosen background before generation."
            )
        oriented = ImageOps.exif_transpose(im)
        iw, ih = oriented.size
    prompt = prompt_file.read_text(encoding="utf-8-sig").strip()
    if not prompt:
        raise ValueError("The motion prompt is empty.")
    if (width is None) != (height is None):
        raise ValueError("Provide both width and height, or neither.")
    if width is None:
        if not 256 <= long_edge <= 3840:
            raise ValueError("Long edge must be between 256 and 3840.")
        scale = long_edge / max(iw, ih)
        width = max(256, int(round(iw * scale / 32)) * 32)
        height = max(256, int(round(ih * scale / 32)) * 32)
    if any(not 256 <= n <= 3840 or n % 32 for n in (width, height)):
        raise ValueError(
            "Dimensions must be multiples of 32 between 256 and 3840; server limits also apply."
        )
    if not math.isfinite(duration) or not 1 <= duration <= 10:
        raise ValueError(
            "This adapter handles short 1-10 second requests; current service limits also apply."
        )
    if audio_mode not in ("mute", "model"):
        raise ValueError("Audio mode must be mute or model.")
    return {
        "image": str(image),
        "image_sha256": sha(image),
        "image_dimensions": [iw, ih],
        "prompt_file": str(prompt_file),
        "prompt": prompt,
        "duration": duration,
        "width": width,
        "height": height,
        "seed": seed,
        "audio_mode": audio_mode,
        "provider": "LTX-2.3 first-frame public demonstration",
        "auth_mode": "anonymous",
        "space": SPACE,
        "base": BASE,
        "method": "First image plus text; no video motion-control input.",
        "requested_aspect_error_fraction": abs((width / height) / (iw / ih) - 1),
    }


def doctor(session=None):
    session = session or requests.Session()
    response = session.get(BASE + "/gradio_api/info", timeout=30)
    response.raise_for_status()
    info = response.json()
    params = info["named_endpoints"]["/generate_video"]["parameters"]
    names = [p["parameter_name"] for p in params]
    if names != PARAMS:
        raise WorkflowError(
            "Provider parameter schema changed; nothing should be uploaded or submitted."
        )
    return {
        "checked_at": now(),
        "service": BASE,
        "schema_matches": True,
        "parameters": names,
        "auth_mode": "anonymous",
        "quota_verified": False,
        "availability_scope": "Schema reachable; generation quota not verified.",
    }


def handoff(plan, out):
    """Prepare a portable local bundle; never sign in, upload, or submit a task."""
    if sha(plan["image"]) != plan["image_sha256"]:
        raise WorkflowError("Input image changed after planning.")
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    image = out / "reference.png"
    with Image.open(plan["image"]) as im:
        ImageOps.exif_transpose(im).convert("RGB").save(image)
    (out / "prompt.txt").write_text(plan["prompt"], encoding="utf-8")
    manifest = {
        "status": "manual_generation_pending",
        "created_at": now(),
        "image": image.name,
        "image_sha256": sha(image),
        "original_image_sha256": plan["image_sha256"],
        "prompt_file": "prompt.txt",
        "requested_settings": {
            k: plan[k] for k in ("duration", "width", "height", "seed", "audio_mode")
        },
        "suggested_space": SPACE,
        "settings_scope": "Suggestions only; confirm current model controls and available quota in the chosen service.",
        "generation_submitted": False,
        "submissions": 0,
        "event_id": None,
        "quota_verified": False,
        "published": False,
    }
    save(out / "handoff.json", manifest)
    (out / "使用说明.txt").write_text(
        "本包只在本地准备了参考图、动作提示词和建议参数，尚未上传或生成。\n"
        "1. 在你选定的图生视频服务中查看可用模型与额度；可参考：\n"
        + SPACE
        + "\n2. 将 reference.png 放入首帧图片输入，粘贴 prompt.txt；"
        "按 handoff.json 中的建议设置一条短镜头，实际参数以页面支持为准。\n"
        "3. 确认账户、模型及费用后只提交一条；保存任务编号或页面结果。"
        "遇到额度不足等待恢复，未知提交先查看已有任务，不连续重试。\n"
        "4. 下载原始 MP4 交回助手，进行完整解码及脸、手、道具、边缘检查；"
        "生成声音是否使用由当前项目决定。\n"
        "浏览器登录不会自动让随包的匿名 Python 客户端使用该账号额度。\n",
        encoding="utf-8",
    )
    return {**manifest, "bundle": str(out)}


def remote_failure_details(value):
    """Classify only explicit provider messages; null errors stay unknown."""
    message = value if isinstance(value, str) else ""
    if isinstance(value, dict):
        message = " ".join(
            value[k] for k in ("error", "message") if isinstance(value.get(k), str)
        )
    text = message.lower()
    quota = ("zerogpu quota" in text or "gpu quota" in text) and any(
        word in text for word in ("exceeded", "exhausted", "not enough", "insufficient")
    )
    countdown = re.search(r"try again in\s+(\d+:\d{2}:\d{2})", message, re.IGNORECASE)
    return {
        "failure_reason_known": bool(message.strip()),
        "failure_category": "quota_exhausted"
        if quota
        else ("remote_error" if message.strip() else "unknown"),
        "provider_retry_after": countdown.group(1) if quota and countdown else None,
        "automatic_retry_at": None,
        "next_action": (
            "Wait for the provider quota reset; no automatic retry or account rotation. Browser sign-in does not authenticate this anonymous client."
            if quota
            else "Inspect the original provider error; do not infer quota exhaustion or resubmit automatically."
        ),
    }


def run_cmd(args):
    p = subprocess.run(
        args, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if p.returncode:
        raise WorkflowError(p.stderr[-2500:] or "Local media command failed.")
    return p.stdout


def probe(video):
    return json.loads(
        run_cmd(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                str(video),
            ]
        )
    )


def check_video(video, out, expected_seconds=None):
    video, out = Path(video).resolve(), Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    meta = probe(video)
    v = next((s for s in meta["streams"] if s["codec_type"] == "video"), None)
    if v is None:
        raise WorkflowError("Output contains no video stream.")
    duration = float(v.get("duration") or meta["format"]["duration"])
    if duration <= 0:
        raise WorkflowError("Output has no playable duration.")
    run_cmd(["ffmpeg", "-v", "error", "-i", str(video), "-f", "null", "-"])
    rate = v.get("avg_frame_rate") or v.get("r_frame_rate", "0/1")
    a, b = (float(x) for x in rate.split("/"))
    fps = a / b if b else 0
    last = max(0, duration - max(1 / fps if fps else 0.1, 0.05))
    samples, small = [], []
    for index, t in enumerate([last * i / 6 for i in range(7)]):
        dest = out / ("frame-%02d.jpg" % index)
        run_cmd(
            [
                "ffmpeg",
                "-v",
                "error",
                "-y",
                "-ss",
                str(t),
                "-i",
                str(video),
                "-frames:v",
                "1",
                str(dest),
            ]
        )
        with Image.open(dest) as im:
            gray = im.convert("L").resize((64, 64))
            small.append(list(gray.getdata()))
        samples.append({"time": t, "image": str(dest)})
    differences = [
        sum(abs(x - y) for x, y in zip(small[i - 1], small[i])) / len(small[i])
        for i in range(1, len(small))
    ]
    warnings = []
    if max(differences, default=0) < 0.25:
        warnings.append(
            "Sampled frames are nearly static; inspect whether requested motion occurred."
        )
    if expected_seconds is not None and abs(duration - expected_seconds) > max(
        0.3, expected_seconds * 0.03
    ):
        warnings.append("Actual duration differs materially from the request.")
    result = {
        "video": str(video),
        "sha256": sha(video),
        "duration_seconds": duration,
        "resolution": [v["width"], v["height"]],
        "fps": fps,
        "audio_present": any(s["codec_type"] == "audio" for s in meta["streams"]),
        "full_decode_pass": True,
        "technical_pass": True,
        "samples": samples,
        "sampled_frame_mean_abs_differences": differences,
        "motion_metric_scope": "Pixel change only; not proof of natural subject motion.",
        "warnings": warnings,
        "model_visual_review": "pending actual inspection",
        "human_playback_review": "pending",
        "published": False,
    }
    save(out / "qa.json", result)
    return result


def file_outputs(value):
    if isinstance(value, dict):
        if (
            value.get("path")
            and value.get("meta", {}).get("_type") == "gradio.FileData"
        ):
            yield value
        for item in value.values():
            yield from file_outputs(item)
    elif isinstance(value, list):
        for item in value:
            yield from file_outputs(item)


def wait_remote(root, receipt, session, wait_seconds):
    if receipt.get("remote_result") is not None:
        return receipt["remote_result"]
    eid = receipt.get("event_id")
    if not eid:
        raise WorkflowError(
            "No confirmed event id; do not resubmit. Inspect the uncertain submission."
        )
    if receipt["status"] == "remote_failed":
        raise WorkflowError(
            "Remote failure already confirmed; this command never creates a new task."
        )
    started = time.monotonic()
    url = BASE + "/gradio_api/call/generate_video/" + eid
    with session.get(url, stream=True, timeout=(30, 120)) as response:
        response.raise_for_status()
        kind = ""
        for line in response.iter_lines(decode_unicode=True, chunk_size=1):
            if time.monotonic() - started > wait_seconds:
                raise TimeoutError(
                    "Bounded remote wait ended; resume the same event later."
                )
            if not line:
                continue
            if line.startswith("event:"):
                kind = line[6:].strip()
            elif line.startswith("data:"):
                value = json.loads(line[5:].strip())
                if kind == "error":
                    update(
                        root,
                        receipt,
                        "remote_failed",
                        remote_error=value,
                        **remote_failure_details(value),
                    )
                    raise WorkflowError(
                        "Remote generation failed: "
                        + json.dumps(value, ensure_ascii=False)
                    )
                if kind == "complete":
                    if not list(file_outputs(value)):
                        update(
                            root,
                            receipt,
                            "remote_failed",
                            remote_error="No file in completion response.",
                        )
                        raise WorkflowError("Completion did not contain video.")
                    update(root, receipt, "generated", remote_result=value)
                    return value
                receipt["last_remote_event"] = kind
                receipt["last_remote_contact_at"] = now()
                save(Path(root) / "receipt.json", receipt)
                event(root, "remote_contact", event=kind)
    raise WorkflowError(
        "Remote stream ended without completion; resume this event, not a new task."
    )


def download(root, receipt, remote, session):
    root = Path(root)
    target = root / "source.mp4"
    if target.exists():
        if not receipt.get("source_sha256") or sha(target) != receipt["source_sha256"]:
            raise WorkflowError(
                "Existing source cannot be verified; preserve it for inspection."
            )
        return target
    output = next(file_outputs(remote))
    url = urljoin(BASE + "/", output.get("url") or "/gradio_api/file=" + output["path"])
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.netloc != urlsplit(BASE).netloc:
        raise WorkflowError("Unexpected media host; inspect before downloading.")
    update(root, receipt, "downloading")
    part = root / "source.mp4.part"
    with session.get(url, stream=True, timeout=(30, 120)) as response:
        response.raise_for_status()
        with part.open("wb") as f:
            for chunk in response.iter_content(65536):
                if chunk:
                    f.write(chunk)
    if not part.stat().st_size:
        raise WorkflowError("Downloaded file is empty.")
    probe(part)
    part.replace(target)
    update(
        root, receipt, "downloaded", source_video=str(target), source_sha256=sha(target)
    )
    return target


def finish(root, receipt, session, wait_seconds=600):
    root = Path(root)
    if receipt.get("source_sha256") and (root / "source.mp4").exists():
        source = root / "source.mp4"
        if sha(source) != receipt["source_sha256"]:
            raise WorkflowError("Preserved source hash changed.")
    else:
        remote = wait_remote(root, receipt, session, wait_seconds)
        source = download(root, receipt, remote, session)
    result = root / "result.mp4"
    if not result.exists():
        temp = root / "result.part.mp4"
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(source), "-map", "0:v:0"]
        if receipt["plan"]["audio_mode"] == "model":
            cmd += ["-map", "0:a?"]
        else:
            cmd += ["-an"]
        cmd += ["-c", "copy", "-movflags", "+faststart", str(temp)]
        run_cmd(cmd)
        temp.replace(result)
    update(root, receipt, "checking")
    qa = check_video(result, root / "qa", receipt["plan"]["duration"])
    if receipt["plan"]["audio_mode"] == "mute" and qa["audio_present"]:
        raise WorkflowError("Expected silent delivery but audio is present.")
    update(
        root,
        receipt,
        "ready",
        video=str(result),
        sha256=qa["sha256"],
        qa=str(root / "qa/qa.json"),
        technical_pass=True,
        model_visual_review="pending actual inspection",
        user_approval="pending",
        published=False,
    )
    return receipt


def failure(root, receipt, exc):
    old = receipt["status"]
    if old in ("prepared", "preflight_passed"):
        state = "preparation_failed"
    elif old == "submitting":
        state = "submission_unknown"
    elif old == "downloading":
        state = "download_interrupted"
    elif old in ("downloaded", "checking"):
        state = "qa_failed"
    elif old == "remote_failed":
        state = old
    elif receipt.get("event_id"):
        state = "wait_interrupted"
    else:
        state = old
    update(root, receipt, state, last_error=str(exc))


def generate(plan, out, session=None, wait_seconds=600):
    if wait_seconds < 1:
        raise ValueError("Wait duration must be positive before submitting.")
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    session = session or requests.Session()
    receipt = {
        "status": "prepared",
        "created_at": now(),
        "updated_at": now(),
        "plan": plan,
        "event_id": None,
        "submissions": 0,
        "auth_mode": "anonymous",
        "automatic_retry": False,
        "user_payment_submitted": False,
        "public_demo_quota_or_cost_guaranteed": False,
        "published": False,
    }
    save(out / "receipt.json", receipt)
    try:
        schema = doctor(session)
        save(out / "provider-check.json", schema)
        update(out, receipt, "preflight_passed")
        if sha(plan["image"]) != plan["image_sha256"]:
            raise WorkflowError("Input image changed after planning.")
        upload_image = out / "input.png"
        with Image.open(plan["image"]) as im:
            ImageOps.exif_transpose(im).convert("RGB").save(upload_image)
        receipt["uploaded_image_sha256"] = sha(upload_image)
        (out / "prompt.txt").write_text(plan["prompt"], encoding="utf-8")
        with upload_image.open("rb") as f:
            response = session.post(
                BASE + "/gradio_api/upload",
                files={"files": ("input.png", f, "image/png")},
                timeout=60,
            )
        response.raise_for_status()
        paths = response.json()
        if (
            not isinstance(paths, list)
            or len(paths) != 1
            or not isinstance(paths[0], str)
        ):
            raise WorkflowError("Upload response schema changed.")
        update(out, receipt, "uploaded")
        first = {
            "path": paths[0],
            "orig_name": "input.png",
            "mime_type": "image/png",
            "meta": {"_type": "gradio.FileData"},
        }
        data = [
            first,
            None,
            None,
            plan["prompt"],
            plan["duration"],
            False,
            plan["seed"],
            False,
            plan["height"],
            plan["width"],
        ]
        update(out, receipt, "submitting", submissions=1, submitted_at=now())
        response = session.post(
            BASE + "/gradio_api/call/generate_video", json={"data": data}, timeout=60
        )
        response.raise_for_status()
        eid = response.json().get("event_id")
        if not isinstance(eid, str) or not eid:
            raise WorkflowError("Submission returned no event id; do not resubmit.")
        update(out, receipt, "submitted", event_id=eid)
        return finish(out, receipt, session, wait_seconds)
    except (Exception, KeyboardInterrupt) as exc:
        failure(out, receipt, exc)
        raise


def resume(out, session=None, wait_seconds=600):
    out = Path(out).resolve()
    receipt = load(out / "receipt.json")
    if receipt["plan"].get("base") != BASE:
        raise WorkflowError(
            "Receipt belongs to a different provider; inspect rather than guessing."
        )
    try:
        return finish(out, receipt, session or requests.Session(), wait_seconds)
    except (Exception, KeyboardInterrupt) as exc:
        failure(out, receipt, exc)
        raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("plan", "generate", "handoff"):
        c = sub.add_parser(name)
        c.add_argument("--image", required=True)
        c.add_argument("--prompt-file", required=True)
        c.add_argument("--duration", type=float, default=6)
        c.add_argument("--width", type=int)
        c.add_argument("--height", type=int)
        c.add_argument("--long-edge", type=int, default=1280)
        c.add_argument("--seed", type=int, default=17)
        c.add_argument("--audio-mode", choices=["mute", "model"], default="mute")
        if name in ("generate", "handoff"):
            c.add_argument("--out")
        if name == "generate":
            c.add_argument("--wait-seconds", type=int, default=600)
    sub.add_parser("doctor")
    for name in ("status", "resume"):
        c = sub.add_parser(name)
        c.add_argument("--run-dir", required=True)
        if name == "resume":
            c.add_argument("--wait-seconds", type=int, default=600)
    c = sub.add_parser("check")
    c.add_argument("--video", required=True)
    c.add_argument("--out", required=True)
    args = p.parse_args()
    try:
        if args.command in ("plan", "generate", "handoff"):
            plan = make_plan(
                args.image,
                args.prompt_file,
                args.duration,
                args.width,
                args.height,
                args.long_edge,
                args.seed,
                args.audio_mode,
            )
            if args.command == "plan":
                result = plan
            else:
                stamp = datetime.now(timezone(timedelta(hours=8))).strftime(
                    "%Y%m%d-%H%M%S-%f"
                )
                folder = (
                    "image-to-video-handoff"
                    if args.command == "handoff"
                    else "image-to-video"
                )
                out = args.out or str(Path.cwd() / "outputs" / folder / stamp)
                result = (
                    handoff(plan, out)
                    if args.command == "handoff"
                    else generate(plan, out, wait_seconds=args.wait_seconds)
                )
        elif args.command == "doctor":
            result = doctor()
        elif args.command == "status":
            result = load(Path(args.run_dir) / "receipt.json")
            result["status_scope"] = (
                "Saved state only; not a live remote/background-worker check."
            )
        elif args.command == "resume":
            result = resume(args.run_dir, wait_seconds=args.wait_seconds)
        else:
            out = Path(args.out).resolve()
            out.mkdir(parents=True, exist_ok=False)
            result = check_video(args.video, out)
        print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    except (Exception, KeyboardInterrupt) as exc:
        print(
            json.dumps(
                {"error": str(exc), "generation_resubmitted": False}, ensure_ascii=False
            ),
            file=sys.stderr,
            flush=True,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
