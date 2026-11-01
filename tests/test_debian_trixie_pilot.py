"""Debian official digest job stays isolated, exact-pinned and no-install."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "scripts/debian-trixie-image-lock.json"


class DebianPilotSafetyTests(unittest.TestCase):
    def test_immutable_arch_specific_official_image(self):
        info = json.loads(LOCK.read_text())
        self.assertEqual(info["schema"], 1)
        self.assertEqual(info["architecture"], "amd64")
        self.assertEqual(info["release"], "trixie")
        self.assertEqual(info["reference_date"], "2026-10-27")
        self.assertRegex(info["digest"], r"^sha256:[a-f0-9]{64}$")
        self.assertEqual(info["publisher"], "docker.io/library/debian")
        self.assertEqual(info["security_status"], "NOT_ASSESSED")
        wf = (ROOT / ".github/workflows/verify.yml").read_text()
        self.assertIn(f"docker.io/library/debian@{info['digest']}", wf)
        self.assertNotIn("image: debian:trixie", wf)

    def test_probe_is_no_install_no_render_no_upload(self):
        wf = (ROOT / ".github/workflows/verify.yml").read_text()
        self.assertIn("  probe-debian-ffmpeg:", wf)
        block = wf.split("  probe-debian-ffmpeg:", 1)[1]
        self.assertIn("if: github.event_name == 'pull_request'", block)
        self.assertIn("runs-on: ubuntu-24.04", block)
        self.assertIn("needs: test", block)
        self.assertIn("VERSION_CODENAME=trixie", block)
        self.assertIn('dpkg --print-architecture', block)
        self.assertIn("docker run --rm", block)
        self.assertIn("--read-only", block)
        self.assertIn("--tmpfs /tmp:rw", block)
        self.assertIn("--cap-drop=ALL", block)
        for required_cap in ("SETUID", "SETGID", "CHOWN", "FOWNER"):
            self.assertIn("--cap-add=" + required_cap, block)
        self.assertEqual(block.count("--cap-add="), 4)
        self.assertIn("--security-opt=no-new-privileges", block)
        self.assertNotIn("--privileged", block)
        self.assertNotIn("/var/run/docker.sock", block)
        self.assertNotIn("container:", block)
        self.assertIn("apt-cache policy ffmpeg", block)
        self.assertIn("SECURITY_STATUS=NOT_ASSESSED", block)
        for forbidden in ("--privileged", "apt-get install",
                          "hyperframes render", "upload-artifact",
                          "curl ", "wget ", "sudo ", "secrets."):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, block)

    def test_manual_media_workflows_unchanged_by_debian_probe(self):
        for filename in ("render.yml", "nounours.yml", "mvc.yml"):
            with self.subTest(filename=filename):
                contents = (ROOT / ".github/workflows" / filename).read_text()
                self.assertIn("  workflow_dispatch:", contents)
                self.assertNotIn("  pull_request:", contents)
                self.assertIn("default: false", contents)
                self.assertNotIn("debian@", contents)


if __name__ == "__main__":
    unittest.main()
