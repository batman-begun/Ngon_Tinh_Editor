from omni_novel_editor.config import BALANCED_MODEL, DEFAULT_MODEL, HIGH_QUALITY_MODEL


def select_model(quality_mode: str) -> str:
    if quality_mode == "Nhanh / tiết kiệm":
        return DEFAULT_MODEL
    if quality_mode == "Chất lượng cao":
        return HIGH_QUALITY_MODEL
    return BALANCED_MODEL
