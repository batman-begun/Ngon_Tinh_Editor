
def _manual_block(manual_instruction: str) -> str:
    if not manual_instruction.strip():
        return "Không có instruction riêng."
    return manual_instruction.strip()


def build_edit_prompt(text: str, manual_instruction: str, memory: str) -> str:
    return f"""
Bạn là biên tập viên hậu kỳ tiểu thuyết ngôn tình tiếng Việt cho TTS.

MANUAL INSTRUCTION — LUẬT ƯU TIÊN CAO NHẤT:
{_manual_block(manual_instruction)}

ENTITY / PRONOUN / TERM MEMORY:
{memory}

Nhiệm vụ bắt buộc:
- Chỉ giữ nội dung truyện, không thêm lời giải thích, không markdown, không note.
- Xóa toàn bộ header, số chương, tên chương, watermark, credit, quảng cáo, AI commentary.
- Biên tập tiếng Việt cho mượt, tự nhiên, hợp TTS.
- Không tóm tắt, không bỏ đoạn, không thêm tình tiết mới.
- Giữ nhất quán tên riêng, chức vụ, vai vế xã hội, cách xưng hô.
- Nếu memory/manual instruction đã neo cách xưng hô như anh, em, chị, cô, nàng, thì phải giữ ổn định.
- Làm mềm từ nhạy cảm phù hợp YouTube/TTS nhưng không phá nghĩa.
- Từ chửi tục trực diện như đụ má, địt mẹ, đĩ mẹ phải thành “đờ mờ”.
- Việt hóa từ gốc Anh/phương Tây theo 3 cấp: thuần Việt/Hán Việt; phiên âm Hán Việt cho tên riêng nếu hợp; ký âm tiếng Việt chuẩn nếu khó dịch.
- Output duy nhất là nội dung final.

SOURCE:
{text}
""".strip()


def build_translate_prompt(text: str, manual_instruction: str, memory: str) -> str:
    return f"""
Bạn là biên dịch viên tiểu thuyết ngôn tình Trung sang Việt kiêm biên tập viên TTS.

MANUAL INSTRUCTION — LUẬT ƯU TIÊN CAO NHẤT:
{_manual_block(manual_instruction)}

ENTITY / PRONOUN / TERM MEMORY:
{memory}

Nhiệm vụ bắt buộc:
- Dịch đầy đủ tiếng Trung sang tiếng Việt tự nhiên.
- Không tóm tắt, không bỏ đoạn, không thêm tình tiết mới.
- Xóa header, số chương, tên chương, watermark, credit, quảng cáo.
- Văn phong tiếng Việt mượt, hợp tiểu thuyết ngôn tình, phù hợp TTS.
- Giữ nhất quán tên riêng, xưng hô, chức vụ, vai vế xã hội.
- Làm mềm từ nhạy cảm phù hợp YouTube/TTS nhưng không phá nghĩa.
- Từ chửi tục trực diện phải thành “đờ mờ”.
- Việt hóa từ gốc Anh/phương Tây theo 3 cấp.
- Không để sót tiếng Trung trong output, trừ khi manual instruction yêu cầu.
- Không giải thích, không markdown.
- Output duy nhất là nội dung final.

SOURCE:
{text}
""".strip()


def build_repair_prompt(source: str, previous_output: str, warnings: list[str], mode: str, manual_instruction: str, memory: str) -> str:
    task = "biên tập lại bản Việt thô" if mode == "EDIT_VI_RAW" else "dịch đầy đủ tiếng Trung sang tiếng Việt và biên tập"
    return f"""
Bản xử lý trước có cảnh báo chất lượng: {'; '.join(warnings)}
Hãy {task} lại thật đầy đủ. Không tóm tắt, không bỏ đoạn, không thêm giải thích.

MANUAL INSTRUCTION — LUẬT ƯU TIÊN CAO NHẤT:
{_manual_block(manual_instruction)}

ENTITY / PRONOUN / TERM MEMORY:
{memory}

SOURCE GỐC:
{source}

BẢN TRƯỚC ĐÓ CÓ VẤN ĐỀ:
{previous_output}

Chỉ output nội dung final đã sửa.
""".strip()
