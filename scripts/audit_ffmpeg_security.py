#!/usr/bin/env python3
"""Audit the *documented*, locally pinned FFmpeg baseline. No network or upgrades.

The advisory reference is reviewed manually; this tool does NOT query Ubuntu
or claim to detect every CVE. It fails if review expires or the manifest drifts.
"""
import argparse
from datetime import date
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "scripts" / "ffmpeg-security-policy.json"
WORKFLOWS = ("render.yml", "mvc.yml", "nounours.yml", "verify.yml")


def validate(policy, *, root=ROOT, today=None):
    """Return (errors, warnings); no side effects."""
    today = today or date.today()
    errors, warnings = [], []
    if policy.get("schema") != 1:
        errors.append("Unsupported security-policy schema")
    version = policy.get("apt_package", "")
    binary = policy.get("ffmpeg_binary", "")
    if not re.fullmatch(r"\d+:[\w.+~-]+", version):
        errors.append("Missing or malformed epoch-qualified Ubuntu APT pin")
    if version.split(":", 1)[-1] != binary:
        errors.append("APT package and expected FFmpeg binary version differ")
    if policy.get("ubuntu_release") != "24.04":
        errors.append("Runner OS and policy release must be reviewed together")

    for name in WORKFLOWS:
        try:
            text = (root / ".github" / "workflows" / name).read_text()
        except OSError as exc:
            errors.append(f"{name} cannot be read: {exc}")
            continue
        pins = re.findall(r"(?m)^\s*sudo apt-get install -y ffmpeg=([^\s#]+)", text)
        # The PR validation workflow has two independent smoke jobs, each with a pin.
        required_count = 2 if name == "verify.yml" else 1
        if pins != [version] * required_count:
            errors.append(f"{name} uses FFmpeg {pins!r}; policy expects {required_count} pin(s) to {version!r}")

    try:
        tool = (root / "scripts" / "check_toolchain.py").read_text()
        actual = re.search(r'(?m)^FFMPEG_BASELINE = "([^"]+)"', tool)
        if not actual or actual.group(1) != binary:
            errors.append("Runtime FFmpeg baseline is inconsistent with security manifest")
    except OSError as exc:
        errors.append(f"Cannot inspect runtime toolchain: {exc}")

    try:
        reviewed = date.fromisoformat(policy["reviewed_on"])
        due = date.fromisoformat(policy["next_review_due"])
        if due < reviewed or (due - reviewed).days > 14:
            errors.append("FFmpeg advisory review interval must not exceed 14 days")
        if today > due:
            errors.append(f"FFmpeg security review overdue since {due.isoformat()}")
        if reviewed > today:
            errors.append("FFmpeg security review date is in the future")
    except (KeyError, ValueError, TypeError) as exc:
        errors.append(f"Invalid security review date: {exc}")

    notice = policy.get("known_security_notice", {})
    if not re.fullmatch(r"USN-\d+-\d+", notice.get("id", "")):
        errors.append("Missing official Ubuntu Security Notice identifier")
    if notice.get("url") != "https://ubuntu.com/security/notices/" + notice.get("id", ""):
        errors.append("Security notice URL and ID disagree")
    fixed = notice.get("fixed_apt_package", "")
    if not fixed or fixed == version:
        errors.append("Missing explicit known newer security-fix version")
    if policy.get("security_status") != "known_gap_unresolved":
        errors.append("Known FFmpeg security gap cannot be silently marked as resolved")

    warnings.append(
        f"FFmpeg pinned {version}, but Ubuntu {notice.get('id', 'USN')} "
        f"documents patched {fixed} via ESM Apps; not installed or verified here. "
        "Manual remediation required. This audit is not a live CVE scan."
    )
    return errors, warnings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", help="Override date YYYY-MM-DD for testing only")
    args = parser.parse_args(argv)
    try:
        policy = json.loads(POLICY.read_text())
        as_of = date.fromisoformat(args.as_of) if args.as_of else date.today()
    except (OSError, ValueError) as exc:
        print(f"FFMPEG POLICY ERROR: {exc}", file=sys.stderr)
        return 1
    errors, warnings = validate(policy, today=as_of)
    for warning in warnings:
        if os.getenv("GITHUB_ACTIONS") == "true":
            print(f"::warning file=scripts/ffmpeg-security-policy.json::{warning}")
        else:
            print("FFMPEG SECURITY WARNING: " + warning)
    for error in errors:
        print("FFMPEG POLICY ERROR: " + error, file=sys.stderr)
    if not errors:
        print(f"FFmpeg security review recorded {policy['reviewed_on']}; next review by {policy['next_review_due']}")
    return int(bool(errors))


if __name__ == "__main__":
    sys.exit(main())
