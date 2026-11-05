"""Fetch the pinned original soundtrack once; never silently substitute music."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

import requests

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "references/template.json"


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, value):
    Path(path).write_text(
        json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def run(args):
    result = subprocess.run(
        args, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode:
        raise RuntimeError(result.stderr[-3000:])
    return result.stdout


def probe(path):
    return json.loads(
        run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                str(path),
            ]
        )
    )


def ensure_music(template=None, cache_dir=None, session=None):
    template = template or load(TEMPLATE)
    music = template["music"]
    expected = music["source_sha256"]
    cache = (
        Path(
            cache_dir
            or os.environ.get("PHOTO_BEAT_CACHE")
            or Path.home() / ".cache/agent-skills/photo-beat-video"
        )
        .expanduser()
        .resolve()
    )
    cache.mkdir(parents=True, exist_ok=True)
    source = cache / (expected + ".mp3")
    session = session or requests.Session()
    if source.exists():
        if sha(source) != expected:
            raise RuntimeError(
                "Cached original soundtrack hash changed; preserve it for inspection. No replacement music used."
            )
    else:
        if not music["download_url"].startswith("https://"):
            raise ValueError("Soundtrack source must use HTTPS.")
        descriptor, temporary = tempfile.mkstemp(
            prefix="music-", suffix=".part", dir=cache
        )
        try:
            with os.fdopen(descriptor, "wb") as stream:
                with session.get(
                    music["download_url"], stream=True, timeout=(15, 45)
                ) as response:
                    response.raise_for_status()
                    size = 0
                    for block in response.iter_content(65536):
                        if block:
                            size += len(block)
                            if size > 10 * 1024 * 1024:
                                raise RuntimeError(
                                    "Unexpectedly large soundtrack response."
                                )
                            stream.write(block)
            if sha(temporary) != expected:
                raise RuntimeError(
                    "Original soundtrack SHA256 mismatch. Source may have changed; no guessed song used."
                )
            Path(temporary).replace(source)
        finally:
            Path(temporary).unlink(missing_ok=True)

    target = cache / (expected + "-aac.m4a")
    receipt_path = target.with_suffix(".json")
    if target.exists():
        if not receipt_path.exists() or sha(target) != load(receipt_path).get("sha256"):
            raise RuntimeError(
                "Cached AAC cannot be verified; preserve it for inspection."
            )
        result = load(receipt_path)
        if result.get("source_sha256") != expected:
            raise RuntimeError("Cached AAC belongs to a different source.")
        return {**result, "path": str(target), "cache_reused": True}

    descriptor, temporary = tempfile.mkstemp(prefix="audio-", suffix=".m4a", dir=cache)
    os.close(descriptor)
    try:
        # Re-encode only for container/player compatibility. No audio filters.
        run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-y",
                "-i",
                str(source),
                "-map",
                "0:a:0",
                "-vn",
                "-c:a",
                "aac",
                "-b:a",
                "256k",
                "-movflags",
                "+faststart",
                temporary,
            ]
        )
        metadata = probe(temporary)
        if not any(stream["codec_type"] == "audio" for stream in metadata["streams"]):
            raise RuntimeError("Fetched source did not yield an audio stream.")
        duration = float(metadata["format"]["duration"])
        if abs(duration - float(music["duration_seconds"])) > 0.15:
            raise RuntimeError(
                "Original soundtrack duration differs from the verified source."
            )
        result = {
            "path": str(target),
            "sha256": sha(temporary),
            "source_sha256": expected,
            "source_url": music["source_page"],
            "duration_seconds": duration,
            "encoding": "MP3 decoded and encoded to AAC; no gain, speed, pitch or fade filters",
            "music_speed_pitch_gain_fades_changed": False,
        }
        Path(temporary).replace(target)
        save(receipt_path, result)
        return {**result, "cache_reused": False}
    finally:
        Path(temporary).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", default=str(TEMPLATE))
    parser.add_argument("--cache-dir")
    args = parser.parse_args()
    try:
        print(
            json.dumps(
                ensure_music(load(args.template), args.cache_dir),
                ensure_ascii=False,
                indent=2,
            )
        )
    except (ValueError, RuntimeError, OSError, requests.RequestException) as exc:
        parser.exit(1, f"Fixed soundtrack unavailable: {exc}\n")


if __name__ == "__main__":
    main()
