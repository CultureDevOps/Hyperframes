"""Private visual review must never create images under the public repo."""
from pathlib import Path
import os
import tempfile
import unittest
from unittest.mock import patch

from scripts import private_visual_review as review


class PrivateVisualReviewTests(unittest.TestCase):
    def test_frames_and_sheet_are_local_ffmpeg_commands(self):
        cmd = review.frame_command(Path("/tmp/sample.mp4"), Path("/tmp/frame_01.png"), 10, 0.05)
        self.assertEqual(cmd[0], "ffmpeg")
        self.assertEqual(cmd[cmd.index("-ss") + 1], "0.500")
        self.assertNotIn("http", " ".join(cmd))
        tile = review.contact_sheet_command(Path("/tmp/private"))
        self.assertIn("tile=3x3:padding=8:margin=8:color=black", tile)
        self.assertEqual(len(review.SAMPLES), 9)

    def test_public_repository_directory_rejected(self):
        with self.assertRaisesRegex(ValueError, "public repository"):
            review.private_root(review.REPO_ROOT / "renders" / "private")

    def test_private_destination_and_reject_public_existing_directory(self):
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d) / "review"
            self.assertEqual(review.private_root(folder), folder.resolve())
            if os.name == "posix":
                self.assertEqual(folder.stat().st_mode & 0o777, 0o700)
                folder.chmod(0o755)
                with self.assertRaisesRegex(ValueError, "accessible to other users"):
                    review.private_root(folder)

    def test_source_hash_is_stable(self):
        with tempfile.TemporaryDirectory() as d:
            filename = Path(d) / "one.mp4"
            filename.write_bytes(b"private test source")
            self.assertEqual(review.sha256_file(filename), __import__("hashlib").sha256(b"private test source").hexdigest())

    def test_malformed_mp4_rejected_without_ffmpeg(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "bad.mp4"
            path.write_bytes(b"not really an mp4")
            with patch.object(review, "probe", return_value={"streams": [], "format": {}}):
                with self.assertRaisesRegex(ValueError, "MP4 contract failed"):
                    review.review(path, seconds=10, directory=Path(d) / "private")
            self.assertFalse((Path(d) / "private").exists())


if __name__ == "__main__":
    unittest.main()
