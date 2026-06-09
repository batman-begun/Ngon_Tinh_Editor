import re
from dataclasses import dataclass

from omni_novel_editor.cleanup.foreign_terms import detect_unresolved_foreign_terms

CJK_RE = re.compile(r"[\u3400-\u9fff]")


@dataclass
class ValidationResult:
    ok: bool
    warnings: list[str]


def validate_output(source: str, output: str, mode: str) -> ValidationResult:
    warnings: list[str] = []
    source_len = len(source or "")
    output_len = len(output or "")
    if source_len > 500:
        ratio = output_len / max(source_len, 1)
        if mode == "EDIT_VI_RAW" and ratio < 0.55:
            warnings.append("Output ngắn bất thường so với bản Việt thô, có nguy cơ bị hụt đoạn.")
        if mode == "TRANSLATE_ZH_TO_VI" and ratio < 0.75:
            warnings.append("Output dịch ngắn bất thường so với source tiếng Trung, có nguy cơ bị hụt đoạn.")
    cjk_count = len(CJK_RE.findall(output or ""))
    if cjk_count > 10:
        warnings.append(f"Output còn {cjk_count} ký tự Hán, có thể dịch chưa sạch.")
    foreign_terms = detect_unresolved_foreign_terms(output or "")
    if foreign_terms:
        warnings.append("Còn foreign terms chưa Việt hóa: " + ", ".join(foreign_terms[:10]))
    return ValidationResult(ok=not warnings, warnings=warnings)
