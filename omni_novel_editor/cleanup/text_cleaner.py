from omni_novel_editor.cleanup.header_cleaner import remove_headers_and_meta
from omni_novel_editor.cleanup.profanity_cleaner import soften_profanity
from omni_novel_editor.cleanup.punctuation_cleaner import clean_punctuation_for_tts
from omni_novel_editor.dictionary.rules import apply_dictionary_rules


def _clean(text: str) -> str:
    result = remove_headers_and_meta(text or "")
    # Dictionary mặc định là layer regex/code thô ưu tiên strict theo CSV user
    # cung cấp. Chạy trước safety cleaner để các mapping như tự tử -> quyên sinh
    # hoặc ma túy -> chất bột trắng thắng mapping mặc định cũ.
    result = apply_dictionary_rules(result)
    result = soften_profanity(result)
    result = clean_punctuation_for_tts(result)
    # LLM đôi khi tự thêm lại dấu nháy/foreign token; pass cuối giúp enforce
    # dictionary sau khi text đã được normalize punctuation.
    result = apply_dictionary_rules(result)
    result = clean_punctuation_for_tts(result)
    return result


def pre_clean(text: str) -> str:
    return _clean(text)


def post_clean(text: str) -> str:
    return _clean(text)
