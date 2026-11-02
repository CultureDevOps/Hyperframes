"""Offline regression tests for neural narration policy (no model download)."""
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from ops010_voice import SIWIS_SHA256, load_voice, verify_piper_model
from ops010_pronunciation import read_lexicon, speech_for_fr_it

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


    def test_curated_mit_upstream_and_local_french_overrides(self):
        data=read_lexicon()
        self.assertEqual(data["source"]["commit"],"138cb7e717d3f73e3aa80d879a99a2ebd989981f")
        self.assertEqual(data["source"]["license"],"MIT")
        terms={x["term"]:x for x in data["entries"]}
        self.assertEqual(terms["GitLab"]["origin"]["ipa"],"/ˈɡɪtˌlæb/")
        self.assertEqual(terms["GitHub"]["origin"]["respelling_us"],"git hub")
        self.assertEqual(terms["HUB"]["origin"]["kind"],"local_french_override")
        self.assertEqual(terms["ChatGPT"]["origin"]["kind"],"local_french_override")
        self.assertTrue(all(x["status"]=="trial_unreviewed" for x in terms.values()))

    def test_french_technical_sentence_and_token_boundaries(self):
        original="Le HUB vérifie GitLab, GitHub et la CI/CD. Docker et Kubernetes."
        speech=speech_for_fr_it(original)
        self.assertIn("heub",speech)
        self.assertIn("guite lab",speech)
        self.assertIn("guite heub",speech)
        self.assertIn("cé i cé dé",speech)
        self.assertIn("dokeur",speech)
        self.assertIn("koubeurnétisse",speech)
        self.assertEqual(original,"Le HUB vérifie GitLab, GitHub et la CI/CD. Docker et Kubernetes.")
        self.assertEqual(speech_for_fr_it("GitLab GitLab"),"guite lab guite lab")
        self.assertEqual(speech_for_fr_it("préGitLab GitLabo HUBris"),"préGitLab GitLabo HUBris")
        self.assertEqual(speech_for_fr_it(" "), " ")

    def test_trial_requires_opt_in_and_original_srt(self):
        renderer=(ROOT/"scripts/render_chatgpt_gitlab.py").read_text()
        voice=(ROOT/"scripts/ops010_voice.py").read_text()
        self.assertIn("p.add_argument('--pronunciation-trial'",renderer)
        self.assertIn("engine.pronunciation_trial = True",renderer)
        self.assertIn("cues.append((begin,cursor,phrase))",renderer)
        self.assertIn("default='piper'",renderer)
        self.assertIn("self.pronunciation_trial = False",voice)

if __name__=='__main__':unittest.main()
