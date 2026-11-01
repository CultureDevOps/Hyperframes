#!/usr/bin/env python3
"""Read-only FFmpeg APT candidate probe; NOT a security/CVE scan."""
import json
from pathlib import Path
import re
import subprocess
import sys


def parse_release(raw):
    return {key: value.strip().strip('"').strip("'")
            for line in raw.splitlines() if "=" in line and not line.startswith("#")
            for key, value in [line.split("=", 1)]}


def parse_candidate(raw):
    match = re.search(r"(?m)^\s*Candidate:\s*(\S+)\s*$", raw)
    return match.group(1) if match and match.group(1) != "(none)" else None


def report(release, apt_output):
    info = parse_release(release)
    candidate = parse_candidate(apt_output)
    if info.get("ID") != "ubuntu" or info.get("VERSION_ID") not in ("24.04", "26.04"):
        raise ValueError("Unexpected runner OS")
    if candidate is None:
        raise ValueError("No FFmpeg candidate in standard APT indexes")
    return {"distribution": "ubuntu", "version_id": info["VERSION_ID"],
            "candidate": candidate, "installed": False,
            "security_status": "NOT_ASSESSED"}


def main():
    try:
        distro = Path("/etc/os-release").read_text()
        output = subprocess.run(["apt-cache", "policy", "ffmpeg"],
                                capture_output=True, text=True, check=True, timeout=30).stdout
        data = report(distro, output)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print("FFMPEG CANDIDATE PROBE ERROR: " + str(exc), file=sys.stderr)
        return 1
    print("FFMPEG_APT_CANDIDATE " + json.dumps(data, sort_keys=True))
    print("Probe checks availability ONLY, not CVE fixes or compatibility.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
