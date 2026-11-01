"""Unit tests do not need HyperFrames, ffmpeg or video uploads."""
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from verify_render import validate, main  # noqa: E402


def good_probe():
    return {
        "streams": [
            {"codec_type": "video", "width": 1920, "height": 1080, "avg_frame_rate": "30/1"},
            {"codec_type": "audio", "codec_name": "aac"},
        ],
        "format": {"duration": "10.033"},
    }


class RenderContractTests(unittest.TestCase):
    def test_valid_video(self):
        self.assertEqual(validate(good_probe(), seconds=10), [])

    def test_portrait_regression(self):
        metadata = good_probe()
        metadata["streams"][0].update(width=1080, height=1920)
        self.assertIn("resolution", " ".join(validate(metadata, seconds=10)))

    def test_missing_audio(self):
        metadata = good_probe()
        metadata["streams"].pop()
        self.assertIn("missing audio", " ".join(validate(metadata, seconds=10)))

    def test_wrong_audio_codec(self):
        metadata = good_probe()
        metadata["streams"][1]["codec_name"] = "mp3"
        self.assertIn("audio codec", " ".join(validate(metadata, seconds=10)))

    def test_wrong_frame_rate(self):
        metadata = good_probe()
        metadata["streams"][0]["avg_frame_rate"] = "25/1"
        self.assertIn("frame rate", " ".join(validate(metadata, seconds=10)))

    def test_bad_fraction(self):
        metadata = good_probe()
        metadata["streams"][0]["avg_frame_rate"] = "0/0"
        self.assertIn("invalid frame rate", " ".join(validate(metadata, seconds=10)))

    def test_wrong_duration(self):
        metadata = good_probe()
        metadata["format"]["duration"] = "8.0"
        self.assertIn("duration", " ".join(validate(metadata, seconds=10)))

    def test_missing_duration(self):
        metadata = good_probe()
        metadata["format"].pop("duration")
        self.assertIn("invalid duration", " ".join(validate(metadata, seconds=10)))

    def test_missing_video(self):
        metadata = good_probe()
        metadata["streams"].pop(0)
        self.assertIn("missing video", " ".join(validate(metadata, seconds=10)))

    def test_empty_file_fails_before_probe(self):
        with patch("pathlib.Path.is_file", return_value=False):
            self.assertEqual(main(["no-such-video.mp4", "--seconds", "10"]), 1)


if __name__ == "__main__":
    unittest.main()
