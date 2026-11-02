"""Offline regression tests for neural narration policy (no model download)."""
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from ops010_voice import SIWIS_SHA256, load_voice, verify_piper_model

class NeuralVoiceTests(unittest.TestCase):
    def test_sha_pinned_and_no_implicit_download(self):
        self.assertEqual(len(SIWIS_SHA256),64)
        with self.assertRaisesRegex(ValueError, '--piper-model'):
            load_voice('piper',None)

    def test_reject_untrusted_model_without_external_packages(self):
        with tempfile.TemporaryDirectory() as directory:
            m=pathlib.Path(directory)/'model.onnx'
            m.write_bytes(b'not really a piper model')
            (pathlib.Path(str(m)+'.json')).write_text('{"audio":{"sample_rate":22050},"espeak":{"voice":"fr"}}')
            with self.assertRaisesRegex(ValueError,'checksum mismatch'):
                verify_piper_model(m)

    def test_legacy_backend_explicit_only(self):
        self.assertEqual(type(load_voice('espeak',None)).__name__,'EspeakFrench')
        with self.assertRaisesRegex(ValueError,'Unsupported'):
            load_voice('remote',None)

    def test_renderer_neural_is_default(self):
        source=(ROOT/'scripts/render_chatgpt_gitlab.py').read_text()
        self.assertIn("default='piper'",source)
        self.assertIn('engine.wav(phrase, p)',source)
        self.assertIn("print(f'VOICE_BACKEND=",source)

if __name__=='__main__':unittest.main()
