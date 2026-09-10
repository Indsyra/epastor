from datetime import datetime
import re
import unicodedata

def normalize(text: str) -> str:
    """Lowercase, remove accents"""
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.strip()

def title_mentions_speaker(title: str, name_keywords: list[str]) -> tuple[bool, str]:
    norm_title = normalize(title)
    for keyword in name_keywords:
        if normalize(keyword) in norm_title:
            return True, f"nom trouvé: '{keyword}'"
    return False, "no mention"