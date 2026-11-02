"""OPS-010 French IT pronunciation pilot: substitutions affect speech only.

The source TSV is pinned by Git commit; this is a tiny reviewed derivative
with local, *unvalidated* French TTS suggestions, not an English IPA engine.
"""
from __future__ import annotations
import json
from pathlib import Path
import re

LEXICON_PATH = Path(__file__).with_name("ops010-pronunciation-fr.json")

def read_lexicon(path: Path = LEXICON_PATH) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != 1 or data.get("language") != "fr-FR":
        raise ValueError("Unsupported pronunciation lexicon")
    terms = [item["term"] for item in data["entries"]]
    if len(terms) != len(set(x.casefold() for x in terms)):
        raise ValueError("Duplicate pronunciation entry")
    for item in data["entries"]:
        if not item["tts_fr"].strip() or item["status"] != "trial_unreviewed":
            raise ValueError("Unexpected or empty trial entry")
    return data

def speech_for_fr_it(text: str, lexicon: dict | None = None) -> str:
    """Preserve editable original text; prepare a separate Piper speech string."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    data = read_lexicon() if lexicon is None else lexicon
    mapping = {i["term"].casefold(): i["tts_fr"] for i in data["entries"]}
    if not mapping:
        return text
    # Longest-first: CI/CD must win over CI, and GitHub over generic HUB.
    terms = sorted((i["term"] for i in data["entries"]), key=lambda x: (-len(x), x.casefold()))
    pattern = re.compile(r"(?<!\w)(?:"+"|".join(re.escape(w) for w in terms)+r")(?!\w)", re.IGNORECASE)
    return pattern.sub(lambda m: mapping[m.group().casefold()], text)
