"""Static legal synonym expansion utility."""
from __future__ import annotations
from typing import List
import re

_SYNONYMS = {
    "fundamental": ["constitutional", "basic", "core"],
    "rights": ["liberties", "freedoms", "entitlements"],
    "privacy": ["data protection", "personal liberty", "private life"],
    "equality": ["equal protection", "non-discrimination"],
    "judicial": ["court", "legal"],
    "review": ["scrutiny", "oversight"],
    "writ": ["mandamus", "certiorari", "habeas corpus", "prohibition"],
    "petition": ["plea", "application"],
    "reservation": ["affirmative action", "quota"],
    "structure": ["framework", "architecture"],
}

def _tokens(text: str) -> List[str]:
    return [t.lower() for t in re.findall(r"[A-Za-z]+", text)]

def expand_with_synonyms(query: str) -> List[str]:
    out: List[str] = []
    for tok in _tokens(query):
        out.extend(_SYNONYMS.get(tok, []))
    return out[:20]
