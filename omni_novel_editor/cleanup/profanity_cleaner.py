import re

# Chỉ normalize các câu chửi tục trực diện/ngôi thứ nhất thành "đờ mờ".
# Không normalize các câu cảm thán suồng sã như "vãi thật", "mẹ kiếp",
# "con mẹ nó" vì đổi máy móc thành "đờ mờ" có thể làm sai sắc thái câu.
EXPLICIT_DIRECT_PROFANITY_PATTERNS = [
    r"\bđụ\s*má\b",
    r"\bđịt\s*mẹ\b",
    r"\bđĩ\s*mẹ\b",
]
DIRECT_ABBREVIATION_PATTERNS = [
    r"\bđm+\b(?=\s*[,.!?;:]*\s*(mày|mi|ngươi|ông|bà|con|thằng|đồ)\b)",
    r"\bđc+m+\b(?=\s*[,.!?;:]*\s*(mày|mi|ngươi|ông|bà|con|thằng|đồ)\b)",
]
DIRECT_PROFANITY_RE = re.compile(
    "|".join(EXPLICIT_DIRECT_PROFANITY_PATTERNS + DIRECT_ABBREVIATION_PATTERNS),
    re.IGNORECASE,
)
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
