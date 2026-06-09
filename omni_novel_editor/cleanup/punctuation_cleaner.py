import re

REPLACE_WITH_COMMA = '"\'()`“”‘’（）'
REMOVE_CHARS = "<>[]{}_-_|"


def clean_punctuation_for_tts(text: str) -> str:
    result = text
    result = re.sub(r"[!！]{2,}", "!", result)
    result = re.sub(r"[?？]{2,}", "?", result)
    result = re.sub(r"([!?！？]){2,}", lambda m: "?" if "?" in m.group(0) or "？" in m.group(0) else "!", result)
    result = re.sub(r"(\.{3,}|…+)", ".", result)
    result = result.translate(str.maketrans({char: "," for char in REPLACE_WITH_COMMA}))
    result = result.translate(str.maketrans({char: "" for char in REMOVE_CHARS}))
    result = re.sub(r"\s+([,.!?;:])", r"\1", result)
    result = re.sub(r",\s*([.!?])", r"\1", result)
    result = re.sub(r"([.!?])\s*,", r"\1", result)
    result = re.sub(r",{2,}", ",", result)
    result = re.sub(r"^[,\s]+", "", result)
    result = re.sub(r"\s{2,}", " ", result)
    result = re.sub(r"\n\s+", "\n", result)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()
