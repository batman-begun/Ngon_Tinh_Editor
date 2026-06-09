import re

TERM_MAP = {
    "sofa": "trường kỷ",
    "ai": "trí tuệ nhân tạo",
    "email": "thư điện tử",
    "e-mail": "thư điện tử",
    "ceo": "tổng giám đốc",
    "boss": "ông chủ",
    "server": "máy chủ",
    "mexico": "Mễ Tây Cơ",
    "washington": "Hoa Thịnh Đốn",
    "rolex": "rô lếch",
    "gemini": "giêm mi nai",
}
TOKEN_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9'\-]*\b")
VIETNAMESE_ALLOWLIST = {
    "anh", "em", "chi", "chị", "co", "cô", "ong", "ông", "ba", "bà", "toi", "tôi", "nang", "nàng",
    "han", "hắn", "va", "và", "la", "là", "mot", "một", "hai", "ba", "bon", "bốn",
}


def apply_known_foreign_terms(text: str) -> str:
    def replace(match: re.Match) -> str:
        token = match.group(0)
        mapped = TERM_MAP.get(token.lower())
        return mapped if mapped else token
    return TOKEN_RE.sub(replace, text)


def detect_unresolved_foreign_terms(text: str) -> list[str]:
    found = []
    for token in TOKEN_RE.findall(text):
        lowered = token.lower()
        if lowered in TERM_MAP or lowered in VIETNAMESE_ALLOWLIST:
            continue
        if len(token) <= 2 and token.islower():
            continue
        if token not in found:
            found.append(token)
    return found
