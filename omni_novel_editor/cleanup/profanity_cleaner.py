import re

DIRECT_PROFANITY_PATTERNS = [
    r"\bđụ\s*má\b", r"\bđịt\s*mẹ\b", r"\bđĩ\s*mẹ\b", r"\bđm+\b", r"\bđc+m+\b",
    r"\bvãi\s*lồn\b", r"\bcon\s*mẹ\s*nó\b", r"\bmẹ\s*kiếp\b",
]
DIRECT_PROFANITY_RE = re.compile("|".join(DIRECT_PROFANITY_PATTERNS), re.IGNORECASE)
SAFETY_REPLACEMENTS = {
    "hiếp dâm": "cưỡng đoạt",
    "tự tử": "tự tận",
    "ma túy": "chất trắng",
}


def soften_profanity(text: str) -> str:
    result = DIRECT_PROFANITY_RE.sub("đờ mờ", text)
    for unsafe, safe in SAFETY_REPLACEMENTS.items():
        result = re.sub(rf"\b{re.escape(unsafe)}\b", safe, result, flags=re.IGNORECASE)
    return result
