import re

CHAPTER_MARKERS = [
    re.compile(r"^\s*(chương|chapter)\s+[\wivxlcdm\d]+\s*[:：.\-–—]?", re.IGNORECASE),
    re.compile(r"^\s*(quyển|phần)\s+\S+\s+(chương)\s+\S+", re.IGNORECASE),
    re.compile(r"^\s*第\s*[\d一二三四五六七八九十百千万零〇两]+\s*章"),
]
TITLE_LIKE = re.compile(r"^[^。.!?！？]{1,180}$")
CREDIT_PATTERNS = [
    r"nguồn\s*:", r"dịch\s*bởi", r"editor\s*:", r"team\s*dịch", r"truyện\s*được\s*đăng\s*tại",
    r"ủng\s*hộ", r"follow", r"like", r"subscribe", r"đọc\s*tiếp\s*tại", r"copyright",
    r"all\s*rights\s*reserved", r"wattpad", r"truyenfull", r"metruyencv", r"广告", r"关注",
    r"公众号", r"版权所有", r"来源", r"译者", r"作者",
]
CREDIT_RE = re.compile("|".join(CREDIT_PATTERNS), re.IGNORECASE)
META_PATTERNS = [
    r"^\s*dưới\s+đây\s+là\s+(bản\s+)?(dịch|chỉnh\s*sửa).*",
    r"^\s*sau\s+đây\s+là.*",
    r"^\s*tôi\s+đã\s+(dịch|chỉnh\s*sửa).*",
    r"^\s*lưu\s*ý\s*:.*",
    r"^\s*ghi\s*chú\s*:.*",
    r"^\s*note\s*:.*",
    r"^\s*translator'?s\s+note\s*:.*",
]
META_RE = re.compile("|".join(META_PATTERNS), re.IGNORECASE)


def _is_heading_line(line: str, index: int) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if any(pattern.search(stripped) for pattern in CHAPTER_MARKERS):
        return True
    return False


def remove_headers_and_meta(text: str) -> str:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    output = []
    non_empty_seen = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            output.append(line)
            continue
        if CREDIT_RE.search(stripped) or META_RE.search(stripped):
            continue
        if non_empty_seen < 5 and _is_heading_line(stripped, non_empty_seen):
            non_empty_seen += 1
            continue
        non_empty_seen += 1
        output.append(line)
    cleaned = "\n".join(output)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned
