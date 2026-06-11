from omni_novel_editor.cleanup.foreign_terms import apply_known_foreign_terms
from omni_novel_editor.cleanup.header_cleaner import remove_headers_and_meta
from omni_novel_editor.cleanup.profanity_cleaner import soften_profanity
from omni_novel_editor.cleanup.punctuation_cleaner import clean_punctuation_for_tts


def pre_clean(text: str) -> str:
    result = remove_headers_and_meta(text or "")
    result = soften_profanity(result)
    result = apply_known_foreign_terms(result)
    result = clean_punctuation_for_tts(result)
    return result


def post_clean(text: str) -> str:
    result = remove_headers_and_meta(text or "")
    result = soften_profanity(result)
    result = apply_known_foreign_terms(result)
    result = clean_punctuation_for_tts(result)
    return result
