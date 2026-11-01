"""Regression tests for the observed FFmpeg and Headless Chrome versions."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import check_toolchain as tool


class ToolchainDriftTests(unittest.TestCase):
    def test_version_parsing(self):
        for binary in ("ffmpeg", "ffprobe"):
            self.assertEqual(tool.extract_ffmpeg_version(binary + " version 6.1.1-3ubuntu5 Copyright", binary), tool.FFMPEG_BASELINE)
        self.assertEqual(tool.extract_chrome_version("Headless Chrome 152.0.7977.30"), tool.CHROME_BASELINE)
        self.assertIsNone(tool.extract_chrome_version("invalid"))

    def test_chrome_cache_lookup(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            exe = home / ".cache/hyperframes/chrome/chrome-headless-shell/linux-152.0.7977.30/chrome-headless-shell-linux64/chrome-headless-shell"
            exe.parent.mkdir(parents=True)
            exe.touch()
            self.assertEqual(tool.cached_chrome_candidates(home), [exe])

    def test_known_good_toolchain(self):
        def fake(command):
            if command[0] in ("ffmpeg", "ffprobe"):
                return command[0] + " version 6.1.1-3ubuntu5 Copyright"
            return "Headless Chrome 152.0.7977.30"
        with tempfile.TemporaryDirectory() as tmp, patch.object(tool, "version_output", fake):
            home = Path(tmp)
            exe = home / ".cache/hyperframes/chrome/chrome-headless-shell/linux-152.0.7977.30/chrome-headless-shell-linux64/chrome-headless-shell"
            exe.parent.mkdir(parents=True)
            exe.touch()
            self.assertEqual(tool.verify(check_chrome=True, home=home), 0)

    def test_binary_sha256_matches_file_content(self):
        import hashlib
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "ffmpeg"
            path.write_bytes(b"fixed binary")
            self.assertEqual(tool.binary_sha256(path), hashlib.sha256(b"fixed binary").hexdigest())

    def test_ffmpeg_drift_fails(self):
        with patch.object(tool, "version_output", return_value="ffmpeg version 7.0"):
            self.assertEqual(tool.verify(), 1)


if __name__ == "__main__":
    unittest.main()
