#!/usr/bin/env python3
"""Fail a render if its probed MP4 metadata differs from its delivery contract."""

import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
import subprocess
import sys


def validate(metadata, *, seconds, width=1920, height=1080, fps=30):
    """Return actionable errors; never accept missing or unparsable fields."""
    streams = metadata.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    errors = []
    if video is None:
        errors.append("missing video stream")
    else:
        if (video.get("width"), video.get("height")) != (width, height):
            errors.append(f"resolution {video.get('width')}x{video.get('height')}; expected {width}x{height}")
        frame_rate = video.get("avg_frame_rate") or video.get("r_frame_rate")
        try:
            actual_fps = float(Fraction(frame_rate))
            if not math.isfinite(actual_fps) or abs(actual_fps - fps) > 0.05:
                errors.append(f"frame rate {actual_fps:g}; expected {fps}")
        except (ValueError, TypeError, ZeroDivisionError):
            errors.append(f"invalid frame rate: {frame_rate!r}")
    if audio is None:
        errors.append("missing audio stream")
    elif audio.get("codec_name") != "aac":
        errors.append(f"audio codec {audio.get('codec_name')!r}; expected 'aac'")

    raw_duration = metadata.get("format", {}).get("duration")
    try:
        actual_duration = float(raw_duration)
        if not math.isfinite(actual_duration) or abs(actual_duration - seconds) > 0.25:
            errors.append(f"duration {actual_duration:g}s; expected {seconds}s (+/- 0.25s)")
    except (ValueError, TypeError):
        errors.append(f"invalid duration: {raw_duration!r}")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--seconds", type=float, required=True)
    args = parser.parse_args(argv)
    if not args.video.is_file() or args.video.stat().st_size == 0:
        print(f"Render missing or empty: {args.video}", file=sys.stderr)
        return 1
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(args.video)],
            capture_output=True, text=True, check=True, timeout=30,
        )
        metadata = json.loads(result.stdout)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        print(f"ffprobe failed for {args.video}: {exc}", file=sys.stderr)
        return 1
    errors = validate(metadata, seconds=args.seconds)
    if errors:
        for error in errors:
            print(f"INVALID RENDER: {error}", file=sys.stderr)
        return 1
    print(f"Verified: {args.video} (1920x1080, 30 fps, AAC, {args.seconds:g}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
