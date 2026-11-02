"""Offline voice engine for OPS-010. No network access at synthesis time."""
from __future__ import annotations
import hashlib
import json
import subprocess
import wave
from ops010_pronunciation import speech_for_fr_it
from pathlib import Path

SAMPLE_RATE = 22050
SIWIS_SHA256 = '641d1ab097da2b81128c076810edb052b385decc8be3381814802a64a73baf99'

def verify_piper_model(path: Path) -> Path:
    model = Path(path).resolve(strict=True)
    config = Path(str(model) + '.json')
    if not config.is_file():
        raise ValueError(f'Missing Piper voice config: {config}')
    with model.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if digest != SIWIS_SHA256:
        raise ValueError('Piper model checksum mismatch')
    data = json.loads(config.read_text(encoding='utf8'))
    if data.get('audio', {}).get('sample_rate') != SAMPLE_RATE or data.get('espeak', {}).get('voice') != 'fr':
        raise ValueError('Unexpected Piper voice configuration')
    return model

class PiperFrench:
    """Load the neural voice exactly once for all narration phrases."""
    def __init__(self, model: Path):
        model = verify_piper_model(model)
        try:
            from piper import PiperVoice, SynthesisConfig
        except ImportError as error:
            raise RuntimeError('Install piper-tts==1.8.0 for neural speech') from error
        self.voice = PiperVoice.load(str(model))
        self.settings = SynthesisConfig(length_scale=1.12, noise_scale=0.58, noise_w_scale=0.72)
        self.pronunciation_trial = False

    def wav(self, phrase: str, path: Path) -> None:
        if not phrase.strip():
            raise ValueError('Empty narration')
        with wave.open(str(path), 'wb') as output:
            speech = speech_for_fr_it(phrase) if self.pronunciation_trial else phrase
            self.voice.synthesize_wav(speech, output, self.settings)

class EspeakFrench:
    """Legacy comparison only; not recommended for final distribution."""
    def wav(self, phrase: str, path: Path) -> None:
        subprocess.run(['espeak', '-v', 'fr', '-s', '156', '-a', '145', '-w', str(path), phrase],
                       check=True, stdout=subprocess.DEVNULL)

def load_voice(mode: str, model: Path | None):
    if mode == 'piper':
        if model is None:
            raise ValueError('--piper-model required; never download models implicitly')
        return PiperFrench(model)
    if mode == 'espeak':
        return EspeakFrench()
    raise ValueError(f'Unsupported voice backend: {mode}')
