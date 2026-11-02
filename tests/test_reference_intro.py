"""OPS-010 reference clip: story beats, generated original audio, deterministic timing."""
from html.parser import HTMLParser
from pathlib import Path
import array
import hashlib
import math
import subprocess
import sys
import tempfile
import unittest
import wave

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "compositions/culturedevops/intro/index.html"
SOUND = ROOT / "scripts/generate_soundtrack.py"

class BeatParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.beats = []
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "section" and "data-beat" in values:
            self.beats.append((values["data-beat"], float(values["data-cue-sec"])))

def rms(samples, start, end, rate):
    chunk = samples[int(start * rate):int(end * rate)]
    return math.sqrt(sum(v * v for v in chunk) / len(chunk)) / 32768

class ReferenceClipTests(unittest.TestCase):
    def test_storyboard_has_distinct_readable_beats_and_full_hd_metadata(self):
        content = HTML.read_text(encoding="utf-8")
        parser = BeatParser()
        parser.feed(content)
        self.assertEqual(parser.beats, [
            ("hook", 0.30), ("confidence", 2.60), ("escalation", 5.50),
            ("climax", 7.20), ("resolution", 8.90),
        ])
        self.assertIn('data-duration="10"', content)
        for setting in ('data-width="1920"', 'data-height="1080"', 'data-fps="30"', "data-no-timeline"):
            self.assertIn(setting, content)
        for cue in ("@keyframes intro", "@keyframes build", "@keyframes alarm",
                    "@keyframes flash", "@keyframes payoff", "@keyframes end"):
            self.assertIn(cue, content)
        self.assertIn("ÇA MARCHE", content)
        self.assertIn("ROLLBACK", content)
        self.assertNotIn("https://", content)

    def test_original_pcm_audio_is_deterministic_and_hits_the_climax(self):
        with tempfile.TemporaryDirectory() as folder:
            files = [Path(folder) / "a.wav", Path(folder) / "b.wav"]
            for path in files:
                subprocess.run([sys.executable, str(SOUND), str(path)], check=True,
                               capture_output=True, timeout=30)
            self.assertEqual(hashlib.sha256(files[0].read_bytes()).digest(),
                             hashlib.sha256(files[1].read_bytes()).digest())
            with wave.open(str(files[0]), "rb") as wav:
                self.assertEqual((wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getnframes()),
                                 (1, 2, 22050, 220500))
                samples = array.array("h")
                samples.frombytes(wav.readframes(wav.getnframes()))
            if sys.byteorder != "little":
                samples.byteswap()
            self.assertLessEqual(max(abs(v) for v in samples), 28000)
            self.assertLess(rms(samples, 0, 0.2, 22050), 0.001)
            self.assertGreater(rms(samples, 5.4, 6.4, 22050), 0.025)
            self.assertLess(rms(samples, 7.01, 7.12, 22050), 0.001)
            self.assertGreater(rms(samples, 7.22, 7.55, 22050), 0.055)
            self.assertEqual(samples[-1], 0)

if __name__ == "__main__":
    unittest.main()
