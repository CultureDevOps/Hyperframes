#!/usr/bin/env python3
"""Create a private local storyboard contact sheet from an existing validated MP4.

No networking, uploads, printing image data to logs, or writes into the repo.
Requires ffmpeg and ffprobe on PATH. Run on your own workstation, not CI.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import stat
import subprocess
import sys

if __package__:
    from .verify_render import validate
else:
    from verify_render import validate

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLES = (0.05, 0.16, 0.27, 0.38, 0.50, 0.62, 0.73, 0.84, 0.95)


def private_root(directory):
    target = Path(directory).expanduser().resolve()
    if target == REPO_ROOT or REPO_ROOT in target.parents:
        raise ValueError("Refusing to store review images inside the public repository")
    target.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name == "posix" and (stat.S_IMODE(target.stat().st_mode) & 0o077):
        raise ValueError("Review directory is accessible to other users; use a private 0700 folder")
    return target


def sha256_file(filename):
    digest = hashlib.sha256()
    with Path(filename).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def frame_command(video, target, seconds, fraction):
    return [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
        "-ss", f"{seconds * fraction:.3f}", "-i", str(video),
        "-frames:v", "1", "-vf", "scale=480:-2",
        "-y", str(target),
    ]


def contact_sheet_command(output_dir):
    return [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
        "-framerate", "1", "-start_number", "1",
        "-i", str(output_dir / "frame_%02d.png"),
        "-vf", "tile=3x3:padding=8:margin=8:color=black",
        "-frames:v", "1", "-y", str(output_dir / "contact-sheet.png"),
    ]


def probe(video):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)],
        capture_output=True, text=True, check=True, timeout=30,
    )
    return json.loads(result.stdout)


def review(video, *, seconds, directory):
    video = Path(video).expanduser().resolve(strict=True)
    if not video.is_file() or video.suffix.lower() != ".mp4" or not video.stat().st_size:
        raise ValueError("Expected a nonempty local MP4 file")
    errors = validate(probe(video), seconds=seconds)
    if errors:
        raise ValueError("MP4 contract failed: " + "; ".join(errors))
    dest = private_root(directory)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run = dest / f"review-{stamp}-{secrets.token_hex(4)}"
    run.mkdir(mode=0o700)
    for index, fraction in enumerate(SAMPLES, start=1):
        image = run / f"frame_{index:02d}.png"
        subprocess.run(frame_command(video, image, seconds, fraction), check=True, timeout=60)
        if not image.is_file() or image.stat().st_size == 0:
            raise RuntimeError(f"Missing review frame: {index}")
        if os.name == "posix":
            image.chmod(0o600)
    subprocess.run(contact_sheet_command(run), check=True, timeout=60)
    sheet = run / "contact-sheet.png"
    if not sheet.is_file() or sheet.stat().st_size == 0:
        raise RuntimeError("Missing contact sheet")
    if os.name == "posix":
        sheet.chmod(0o600)
    manifest = {
        "source_name": video.name,
        "source_sha256": sha256_file(video),
        "expected_seconds": seconds,
        "sample_seconds": [round(seconds * fraction, 3) for fraction in SAMPLES],
        "review": "local-only contact sheet; inspect original MP4 for motion and audio",
        "uploaded": False,
    }
    fd = os.open(run / "manifest.json", os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        json.dump(manifest, output, ensure_ascii=False, indent=2)
        output.write("\n")
    return sheet


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mp4", type=Path, help="Existing local MP4, never downloaded from GitHub Actions")
    parser.add_argument("--seconds", required=True, type=float, choices=(10, 35))
    parser.add_argument("--out-root", type=Path, default=Path.home() / ".hyperframes-private-review")
    args = parser.parse_args(argv)
    if args.seconds <= 0:
        parser.error("Duration must be positive")
    previous = os.umask(0o077)
    try:
        sheet = review(args.mp4, seconds=args.seconds, directory=args.out_root)
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        print(f"PRIVATE REVIEW FAILED: {exc}", file=sys.stderr)
        return 1
    finally:
        os.umask(previous)
    print(f"Local contact sheet: {sheet}")
    print("Open the original MP4 locally for motion, sound balance and pacing; never upload it to this public repo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
