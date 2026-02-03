import re
import unicodedata
from difflib import SequenceMatcher


def _normalize_text(s: str) -> str:
    s = (s or "").lower().strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()