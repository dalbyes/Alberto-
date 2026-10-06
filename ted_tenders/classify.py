"""Classifica un bando in una categoria (vigili_del_fuoco / polizia / soccorso /
antinfortunistica_generica / altro) in base al testo del titolo, usando le
stesse parole chiave della ricerca.
"""

from __future__ import annotations

from . import config

_LOWER_KEYWORDS = {
    category: [kw.lower() for kw in keywords]
    for category, keywords in config.KEYWORDS.items()
}


def categorize(title: str) -> str:
    text = (title or "").lower()
    for category, keywords in _LOWER_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return category
    return "altro"
