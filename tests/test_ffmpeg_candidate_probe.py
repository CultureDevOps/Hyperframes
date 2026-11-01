"""Checks that optional FFmpeg APT probe neither installs nor claims security."""
from pathlib import Path
import unittest
from scripts.probe_ffmpeg_apt import parse_candidate, report

ROOT = Path(__file__).resolve().parents[1]


class CandidateTests(unittest.TestCase):
    def test_ubuntu24_and_ubuntu26(self):
        for version, apt in (("24.04", "7:6.1.1-3ubuntu5"), ("26.04", "7:8.0.1-3ubuntu2")):
            with self.subTest(version=version):
                got = report(f'ID=ubuntu\nVERSION_ID="{version}"\n',
                             "ffmpeg:\n Candidate: " + apt + "\n")
                self.assertEqual(got["candidate"], apt)
                self.assertEqual(got["security_status"], "NOT_ASSESSED")
                self.assertIs(got["installed"], False)

    def test_no_candidate(self):
        self.assertIsNone(parse_candidate("ffmpeg:\n Candidate: (none)\n"))
        with self.assertRaises(ValueError):
            report('ID=ubuntu\nVERSION_ID="24.04"\n', " Candidate: (none)\n")

    def test_unexpected_os(self):
        with self.assertRaises(ValueError):
            report('ID=debian\nVERSION_ID="13"\n', " Candidate: 7:7.1.5-0+deb13u1\n")

    def test_new_job_only_looks_up_apt_metadata(self):
        wf = (ROOT / ".github/workflows/verify.yml").read_text()
        self.assertIn("  probe-ubuntu-ffmpeg:", wf)
        self.assertIn("os: [ubuntu-24.04, ubuntu-26.04]", wf)
        block = wf.split("  probe-ubuntu-ffmpeg:", 1)[1]
        self.assertIn("python3 scripts/probe_ffmpeg_apt.py", block)
        self.assertIn("sudo apt-get update -qq", block)
        for forbidden in ("apt-get install", "upload-artifact", "hyperframes render", "docker "):
            self.assertNotIn(forbidden, block)


if __name__ == "__main__":
    unittest.main()
