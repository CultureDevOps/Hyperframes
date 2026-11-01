#!/usr/bin/env python3
"""Detect drift from the verified FFmpeg and HyperFrames bundled-Chrome baseline."""
import argparse
import hashlib
import shutil
from pathlib import Path
import re
import subprocess
import sys

FFMPEG_BASELINE = "6.1.1-3ubuntu5"
CHROME_BASELINE = "152.0.7977.30"


def extract_ffmpeg_version(output, executable):
    match = re.search(r"^" + re.escape(executable) + r" version (\S+)", output, re.MULTILINE)
    return match.group(1) if match else None


def extract_chrome_version(output):
    match = re.search(r"\b(\d+\.\d+\.\d+\.\d+)\b", output)
    return match.group(1) if match else None


def cached_chrome_candidates(home):
    root = home / ".cache" / "hyperframes" / "chrome" / "chrome-headless-shell"
    return sorted(root.glob("linux-*/chrome-headless-shell-linux64/chrome-headless-shell"))


def version_output(command):
    result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=True)
    return result.stdout + result.stderr


def binary_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(*, check_chrome=False, home=None, show_sha256=False):
    errors = []
    for executable in ("ffmpeg", "ffprobe"):
        try:
            actual = extract_ffmpeg_version(version_output([executable, "-version"]), executable)
            if actual != FFMPEG_BASELINE:
                errors.append(f"{executable} version {actual!r}; expected {FFMPEG_BASELINE}")
            else:
                print(f"Verified {executable}: {actual}")
                if show_sha256:
                    resolved = shutil.which(executable)
                    if not resolved:
                        errors.append(f"Cannot locate {executable} for digest")
                    else:
                        try:
                            print(f"SHA256 {executable}: {binary_sha256(resolved)}")
                        except OSError as exc:
                            errors.append(f"Cannot hash {executable}: {exc}")
        except (OSError, subprocess.SubprocessError) as exc:
            errors.append(f"Cannot check {executable}: {exc}")
    if check_chrome:
        chrome = cached_chrome_candidates(home or Path.home())
        if len(chrome) != 1:
            errors.append(f"Expected one HyperFrames cached Chrome, found {len(chrome)}")
        else:
            path_version = chrome[0].parents[1].name.removeprefix("linux-")
            try:
                binary_version = extract_chrome_version(version_output([str(chrome[0]), "--version"]))
                if binary_version != CHROME_BASELINE or path_version != CHROME_BASELINE:
                    errors.append(f"Chrome binary={binary_version!r}, cache={path_version!r}; expected {CHROME_BASELINE}")
                else:
                    print(f"Verified Chrome Headless Shell: {binary_version}")
                    if show_sha256:
                        try:
                            print(f"SHA256 HeadlessChrome: {binary_sha256(chrome[0])}")
                        except OSError as exc:
                            errors.append(f"Cannot hash Chrome: {exc}")
            except (OSError, subprocess.SubprocessError) as exc:
                errors.append(f"Cannot check Chrome: {exc}")
    for error in errors:
        print("TOOLCHAIN DRIFT: " + error, file=sys.stderr)
    return 1 if errors else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-chrome", action="store_true")
    parser.add_argument("--show-sha256", action="store_true", help="Print local executable hashes for audit; not signatures")
    args = parser.parse_args(argv)
    return verify(check_chrome=args.check_chrome, show_sha256=args.show_sha256)


if __name__ == "__main__":
    sys.exit(main())
