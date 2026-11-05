"""Portable photo rhythm rendering with pinned music and actual video-frame freezes."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
from pathlib import Path
import subprocess
import time

from PIL import Image, ImageFilter, ImageOps

from music_cache import TEMPLATE, ensure_music, load, probe, run, save, sha


def require_photo(path):
    path = Path(path).resolve()
    with Image.open(path) as image:
        if getattr(image, "is_animated", False):
            raise ValueError(
                "This photo template needs static images; choose a frame explicitly for an animation."
            )
        image.verify()
    return {"path": str(path), "sha256": sha(path)}


def create_plan(
    inputs,
    styled=(),
    motion=None,
    *,
    mode="photos",
    template=None,
    duration=None,
    width=1080,
    height=1920,
    fps=30,
    motion_start=0,
    motion_duration=None,
    speed=0.8,
    max_opening=3,
    styled_seconds=1.3,
):
    template = template or load(TEMPLATE)
    if not inputs:
        raise ValueError("At least one uploaded photo is required.")
    if width < 64 or height < 64 or width % 2 or height % 2 or not 1 <= fps <= 60:
        raise ValueError(
            "Use even dimensions of at least 64 pixels and a frame rate from 1 to 60."
        )
    if max_opening < 1:
        raise ValueError("Opening photo limit must be positive.")
    originals = [require_photo(path) for path in inputs]
    styles = [require_photo(path) for path in styled]
    shots = []
    cursor = 0
    beats = [float(t) for t in template["beat_times"]]

    def append(kind, asset, seconds):
        nonlocal cursor
        frames = max(1, round(seconds * fps))
        shots.append(
            {
                "kind": kind,
                **asset,
                "start_frame": cursor,
                "frames": frames,
                "end_frame_exclusive": cursor + frames,
            }
        )
        cursor += frames

    if mode == "photos":
        if styles or motion:
            raise ValueError(
                "Styled stills and person motion require --mode sweet-cool."
            )
        total = 14.0 if duration is None else duration
        if not math.isfinite(total) or not 0 < total <= float(
            template["music"]["duration_seconds"]
        ):
            raise ValueError("Duration must fit the fixed soundtrack.")
        total_frames = round(total * fps)
        if total_frames < len(originals):
            raise ValueError("Each photo needs at least one output frame.")
        for i, asset in enumerate(originals):
            # Snap cuts to nearby known onsets without dropping any original photo.
            target = (i + 1) * total_frames / len(originals)
            end = (
                total_frames
                if i == len(originals) - 1
                else min(
                    (
                        round(t * fps)
                        for t in beats
                        if cursor
                        < round(t * fps)
                        <= total_frames - (len(originals) - i - 1)
                        and abs(round(t * fps) - target) <= fps * 0.15
                    ),
                    key=lambda frame: abs(frame - target),
                    default=round(target),
                )
            )
            end = max(cursor + 1, min(end, total_frames - (len(originals) - i - 1)))
            append("original", asset, (end - cursor) / fps)
        omitted = []
    elif mode == "sweet-cool":
        if not styles or motion is None:
            raise ValueError(
                "Full sweet-cool requires generated whole images and a real motion clip; no silent photo-only fallback."
            )
        if not math.isfinite(styled_seconds) or styled_seconds <= 0:
            raise ValueError("Styled image hold duration must be finite and positive.")
        if duration is not None:
            raise ValueError(
                "Full-template duration follows actual motion and stills; adjust the motion interval instead."
            )
        if (
            not all(math.isfinite(x) for x in (motion_start, speed))
            or motion_start < 0
            or not 0.25 <= speed <= 2
        ):
            raise ValueError("Invalid motion start or playback speed.")
        motion = Path(motion).resolve()
        metadata = probe(motion)
        stream = next(
            (s for s in metadata["streams"] if s["codec_type"] == "video"), None
        )
        if stream is None:
            raise ValueError("Motion source has no video stream.")
        available = float(stream.get("duration") or metadata["format"]["duration"])
        take = (
            min(3.6 * speed, available - motion_start)
            if motion_duration is None
            else motion_duration
        )
        if (
            not math.isfinite(take)
            or take <= 0
            or motion_start + take > available + 0.001
        ):
            raise ValueError(
                "Requested motion interval exceeds the real source; no loops or fake frames added."
            )
        chosen = originals[:max_opening]
        omitted = originals[max_opening:]
        for asset in chosen:
            append("original", asset, 4.2 / len(chosen))
        for asset in styles:
            append("styled", asset, styled_seconds)
        append(
            "motion",
            {
                "path": str(motion),
                "sha256": sha(motion),
                "source_start": motion_start,
                "source_duration": take,
                "speed": speed,
            },
            take / speed,
        )
        append(
            "freeze", {"source": "last decoded frame of the selected motion clip"}, 2.4
        )
        if cursor / fps > float(template["music"]["duration_seconds"]):
            raise ValueError("Selected edit exceeds the original soundtrack.")
    else:
        raise ValueError("Unknown template mode.")
    return {
        "schema_version": 1,
        "mode": mode,
        "width": width,
        "height": height,
        "fps": fps,
        "frames": cursor,
        "duration_seconds": cursor / fps,
        "shots": shots,
        "beat_times": beats,
        "omitted_opening_photos": omitted,
        "soundtrack": template["music"]["source_page"],
        "original_photos_preserved": True,
        "generated_audio_used": False,
        "planning_scope": "Offline plan only; no music downloaded or AI generation submitted",
    }


def fit_image(image, width, height):
    image = ImageOps.exif_transpose(image).convert("RGBA")
    neutral = Image.new("RGBA", image.size, (250, 243, 233, 255))
    neutral.alpha_composite(image)
    image = neutral.convert("RGB")
    background = ImageOps.fit(image, (width, height)).filter(
        ImageFilter.GaussianBlur(max(2, width / 40))
    )
    # Leave room for the whole-frame pulse without clipping shoes or objects.
    foreground = ImageOps.contain(
        image, (round(width * 0.96), round(height * 0.96)), Image.Resampling.LANCZOS
    )
    background.paste(
        foreground, ((width - foreground.width) // 2, (height - foreground.height) // 2)
    )
    return background


def effect(image, frame, shot, beats, fps):
    elapsed = [
        (frame - round(t * fps)) / fps
        for t in beats
        if shot["start_frame"] <= round(t * fps) <= frame
    ]
    kick = max((math.exp(-t / 0.10) for t in elapsed if t < 0.4), default=0)
    original = shot["kind"] == "original"
    zoom = 1 if original else 1 + 0.012 * kick
    result = image
    if zoom != 1:
        width, height = image.size
        inv = 1 / zoom
        result = image.transform(
            image.size,
            Image.Transform.AFFINE,
            (
                inv,
                0,
                width * (1 - inv) / 2,
                0,
                inv,
                height * (1 - inv) / 2 + 2 * kick * inv,
            ),
            Image.Resampling.BICUBIC,
        )
    flash = (0.10 if original else 0.14) * kick
    if flash > 0.001:
        result = Image.blend(
            result, Image.new("RGB", image.size, (255, 247, 235)), flash
        )
    return result


def audio_packets(path):
    data = json.loads(
        run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_packets",
                "-show_data_hash",
                "sha256",
                "-show_entries",
                "packet=data_hash",
                "-of",
                "json",
                str(path),
            ]
        )
    )
    return [p["data_hash"] for p in data["packets"]]


def prepare_motion(shot, plan, out):
    width, height, fps = plan["width"], plan["height"], plan["fps"]
    fw, fh = max(2, int(width * 0.96) // 2 * 2), max(2, int(height * 0.96) // 2 * 2)
    target = out / "selected-motion.mp4"
    graph = (
        f"[0:v]setpts=(PTS-STARTPTS)/{shot['speed']},fps={fps},split[b][f];"
        f"[b]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},boxblur=12:2[bg];"
        f"[f]scale={fw}:{fh}:force_original_aspect_ratio=decrease:force_divisible_by=2[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1,format=yuv420p[v]"
    )
    run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-n",
            "-ss",
            str(shot["source_start"]),
            "-t",
            str(shot["source_duration"]),
            "-i",
            shot["path"],
            "-filter_complex",
            graph,
            "-map",
            "[v]",
            "-an",
            "-frames:v",
            str(shot["frames"]),
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "18",
            str(target),
        ]
    )
    actual = probe(target)["streams"][0]
    if int(actual.get("nb_frames", -1)) != shot["frames"]:
        raise RuntimeError(
            "Selected motion produced too few frames. Choose a valid source interval; no duplicated frames inserted."
        )
    return target


def read_frame(stream, size):
    result = bytearray()
    while len(result) < size:
        chunk = stream.read(size - len(result))
        if not chunk:
            raise RuntimeError("Motion decoder ended before the planned last frame.")
        result.extend(chunk)
    return bytes(result)


def check_output(video, plan, audio, out):
    qa_dir = out / "qa"
    qa_dir.mkdir()
    run(["ffmpeg", "-v", "error", "-i", str(video), "-f", "null", "-"])
    metadata = probe(video)
    v = next(s for s in metadata["streams"] if s["codec_type"] == "video")
    a = next(s for s in metadata["streams"] if s["codec_type"] == "audio")
    packets = audio_packets(video)
    same_audio = bool(packets) and packets == audio_packets(audio)[: len(packets)]
    video_seconds = float(v["duration"])
    audio_seconds = float(a["duration"])
    timing = abs(video_seconds - plan["duration_seconds"]) <= 1 / plan["fps"] + 0.001
    sync = abs(video_seconds - audio_seconds) <= 0.10
    shape = (v["width"], v["height"]) == (plan["width"], plan["height"])
    samples = {0, plan["frames"] - 1}
    for shot in plan["shots"]:
        samples.update(
            (
                shot["start_frame"],
                shot["end_frame_exclusive"] - 1,
                shot["start_frame"] + shot["frames"] // 2,
            )
        )
        if shot["start_frame"]:
            samples.add(shot["start_frame"] - 1)
    frames = sorted(samples)
    selection = "+".join(f"eq(n,{f})" for f in frames)
    run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-n",
            "-i",
            str(video),
            "-an",
            "-vf",
            f"select='{selection}',scale=270:-2",
            "-fps_mode",
            "vfr",
            "-q:v",
            "3",
            str(qa_dir / "frame-%03d.jpg"),
        ]
    )
    volume = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(video),
            "-vn",
            "-af",
            "volumedetect,silencedetect=n=-50dB:d=0.5",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    audio_observations = [
        line.strip()
        for line in volume.stderr.splitlines()
        if any(
            k in line
            for k in ("mean_volume:", "max_volume:", "silence_start:", "silence_end:")
        )
    ]
    if volume.returncode:
        raise RuntimeError("Audio analysis failed.")
    result = {
        "full_decode_pass": True,
        "audio_cache_prefix_packets_match": same_audio,
        "source_audio_packet_count": len(packets),
        "duration_pass": timing,
        "av_sync_pass": sync,
        "dimensions_pass": shape,
        "video_seconds": video_seconds,
        "audio_seconds": audio_seconds,
        "audio_observations": audio_observations,
        "samples": [
            {"frame": f, "path": str(qa_dir / f"frame-{i + 1:03d}.jpg")}
            for i, f in enumerate(frames)
        ],
        "technical_pass": same_audio and timing and sync and shape,
        "model_visual_review": "pending actual inspection",
        "user_aesthetic_approval": "pending",
    }
    save(qa_dir / "qa.json", result)
    if not result["technical_pass"]:
        raise RuntimeError("Output failed technical checks; inspect qa/qa.json.")
    return result


def render(plan, audio_info, out):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    video = out / "result.mp4"
    receipt = {
        "status": "prepared",
        "published": False,
        "active_remote_job": False,
        "model_visual_review": "pending actual inspection",
        "user_aesthetic_approval": "pending",
    }
    save(out / "plan.json", plan)
    save(out / "delivery.json", receipt)
    encoder = decoder = None
    try:
        audio = Path(audio_info["path"])
        if sha(audio) != audio_info["sha256"]:
            raise RuntimeError("Cached audio changed after verification.")
        width, height, fps = plan["width"], plan["height"], plan["fps"]
        bases = {}
        for shot in plan["shots"]:
            if "path" in shot and sha(shot["path"]) != shot["sha256"]:
                raise RuntimeError("A selected input changed after planning.")
            if shot["kind"] in ("original", "styled") and shot["path"] not in bases:
                with Image.open(shot["path"]) as image:
                    bases[shot["path"]] = fit_image(image, width, height)
            if shot["kind"] == "motion":
                selected = prepare_motion(shot, plan, out)
        receipt["status"] = "rendering"
        save(out / "delivery.json", receipt)
        with (out / "render.log").open("w", encoding="utf-8") as log:
            encoder = subprocess.Popen(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-n",
                    "-f",
                    "rawvideo",
                    "-pix_fmt",
                    "rgb24",
                    "-s",
                    f"{width}x{height}",
                    "-r",
                    str(fps),
                    "-i",
                    "-",
                    "-i",
                    str(audio),
                    "-map",
                    "0:v:0",
                    "-map",
                    "1:a:0",
                    "-t",
                    str(plan["duration_seconds"]),
                    "-vf",
                    "scale=in_range=pc:out_range=tv:out_color_matrix=bt709",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "fast",
                    "-crf",
                    "18",
                    "-pix_fmt",
                    "yuv420p",
                    "-color_primaries",
                    "bt709",
                    "-color_trc",
                    "bt709",
                    "-colorspace",
                    "bt709",
                    "-c:a",
                    "copy",
                    "-movflags",
                    "+faststart",
                    str(video),
                ],
                stdin=subprocess.PIPE,
                stderr=log,
            )
            last = None
            started = time.monotonic()
            for shot in plan["shots"]:
                if shot["kind"] == "motion":
                    decoder = subprocess.Popen(
                        [
                            "ffmpeg",
                            "-v",
                            "error",
                            "-i",
                            str(selected),
                            "-an",
                            "-f",
                            "rawvideo",
                            "-pix_fmt",
                            "rgb24",
                            "-",
                        ],
                        stdout=subprocess.PIPE,
                        stderr=log,
                    )
                for frame in range(shot["start_frame"], shot["end_frame_exclusive"]):
                    if shot["kind"] == "motion":
                        pixels = read_frame(decoder.stdout, width * height * 3)
                        last = Image.frombytes("RGB", (width, height), pixels)
                    else:
                        base = last if shot["kind"] == "freeze" else bases[shot["path"]]
                        if base is None:
                            raise RuntimeError(
                                "Freeze needs an actual preceding video frame."
                            )
                        pixels = effect(
                            base, frame, shot, plan["beat_times"], fps
                        ).tobytes()
                    encoder.stdin.write(pixels)
                    if frame % max(1, fps * 3) == 0:
                        print(
                            json.dumps(
                                {
                                    "stage": "rendering",
                                    "frame": frame,
                                    "total": plan["frames"],
                                    "elapsed_seconds": round(
                                        time.monotonic() - started, 1
                                    ),
                                }
                            ),
                            flush=True,
                        )
                if decoder:
                    decoder.stdout.close()
                    if decoder.wait():
                        raise RuntimeError(
                            "Motion decoding failed; inspect render.log."
                        )
                    decoder = None
            encoder.stdin.close()
            if encoder.wait():
                raise RuntimeError("Rendering failed; inspect render.log.")
            encoder = None
        qa = check_output(video, plan, audio, out)
        receipt.update(
            status="ready",
            video=str(video),
            sha256=sha(video),
            duration_seconds=plan["duration_seconds"],
            resolution=[width, height],
            fps=fps,
            technical_pass=qa["technical_pass"],
            music=audio_info,
            audio_cache_prefix_packets_match=True,
            music_speed_pitch_gain_fades_changed=False,
            generated_audio_used=False,
            motion_video_used=plan["mode"] == "sweet-cool",
            qa=str(out / "qa/qa.json"),
        )
    except BaseException as exc:
        receipt.update(status="failed", error=str(exc), technical_pass=False)
        raise
    finally:
        for child in (decoder, encoder):
            if child and child.poll() is None:
                child.kill()
                child.wait()
            if child and child.stdout:
                child.stdout.close()
            if child and child.stdin and not child.stdin.closed:
                try:
                    child.stdin.close()
                except OSError:
                    pass
        save(out / "delivery.json", receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "make"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--input", action="append", required=True)
        cmd.add_argument("--styled", action="append", default=[])
        cmd.add_argument("--motion")
        cmd.add_argument("--mode", choices=["photos", "sweet-cool"], default="photos")
        cmd.add_argument("--template", default=str(TEMPLATE))
        cmd.add_argument("--duration", type=float)
        cmd.add_argument("--width", type=int, default=1080)
        cmd.add_argument("--height", type=int, default=1920)
        cmd.add_argument("--fps", type=int, default=30)
        cmd.add_argument("--motion-start", type=float, default=0)
        cmd.add_argument("--motion-duration", type=float)
        cmd.add_argument("--speed", type=float, default=0.8)
        cmd.add_argument("--max-opening", type=int, default=3)
        cmd.add_argument("--styled-seconds", type=float, default=1.3)
        if name == "make":
            cmd.add_argument("--cache-dir")
            cmd.add_argument("--out")
    args = parser.parse_args()
    try:
        template = load(args.template)
        plan = create_plan(
            args.input,
            args.styled,
            args.motion,
            mode=args.mode,
            template=template,
            duration=args.duration,
            width=args.width,
            height=args.height,
            fps=args.fps,
            motion_start=args.motion_start,
            motion_duration=args.motion_duration,
            speed=args.speed,
            max_opening=args.max_opening,
            styled_seconds=args.styled_seconds,
        )
        if args.command == "plan":
            result = plan
        else:
            out = Path(
                args.out
                or Path.cwd()
                / "outputs/photo-beat-video"
                / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            )
            if out.exists():
                raise FileExistsError(
                    "Output directory exists; prior versions will not be overwritten."
                )
            audio = ensure_music(template, args.cache_dir)
            result = render(plan, audio, out)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, RuntimeError, OSError) as exc:
        parser.exit(1, f"Cannot complete photo beat video: {exc}\n")


if __name__ == "__main__":
    main()
