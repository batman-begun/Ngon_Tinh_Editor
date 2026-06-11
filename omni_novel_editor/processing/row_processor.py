from dataclasses import dataclass

from omni_novel_editor.cleanup.text_cleaner import post_clean, pre_clean
from omni_novel_editor.dictionary.rules import apply_dictionary_rules, build_dictionary_prompt_block, load_builtin_dictionary
from omni_novel_editor.excel.workbook import cell_text, set_cell_text
from omni_novel_editor.llm.prompts import build_edit_prompt, build_repair_prompt, build_translate_prompt
from omni_novel_editor.processing.chunker import chunk_text
from omni_novel_editor.validation.output_checks import validate_output


@dataclass
class RowResult:
    row: int
    status: str
    mode: str
    output: str = ""
    error: str = ""
    warnings: list[str] | None = None
    chunks: int = 0


def select_source(workbook, sheet_name: str, row: int, vietnamese_col: str, chinese_col: str) -> tuple[str, str]:
    vietnamese = cell_text(workbook, sheet_name, row, vietnamese_col)
    if vietnamese.strip():
        return "EDIT_VI_RAW", vietnamese
    chinese = cell_text(workbook, sheet_name, row, chinese_col)
    if chinese.strip():
        return "TRANSLATE_ZH_TO_VI", chinese
    return "SKIP_EMPTY", ""


def process_row(
    workbook,
    sheet_name: str,
    row: int,
    columns: dict[str, str],
    output_col: str,
    llm_client,
    manual_instruction: str,
    memory_prompt: str,
    max_chars: int,
    repair_enabled: bool,
) -> RowResult:
    mode, source = select_source(workbook, sheet_name, row, columns.get("vietnamese_raw", ""), columns.get("chinese_source", ""))
    if mode == "SKIP_EMPTY":
        return RowResult(row=row, status="skipped", mode=mode, error="Không có nội dung ở cột nguồn.")

    dictionary_rules = load_builtin_dictionary()
    cleaned_source = apply_dictionary_rules(pre_clean(source), dictionary_rules)
    chunks = chunk_text(cleaned_source, max_chars=max_chars)
    outputs: list[str] = []
    warnings: list[str] = []

    for chunk in chunks:
        dictionary_block = build_dictionary_prompt_block(chunk, dictionary_rules)
        prompt = build_edit_prompt(chunk, manual_instruction, memory_prompt, dictionary_block) if mode == "EDIT_VI_RAW" else build_translate_prompt(chunk, manual_instruction, memory_prompt, dictionary_block)
        raw_output = llm_client.generate(prompt)
        final_output = apply_dictionary_rules(post_clean(raw_output), dictionary_rules)
        final_output = post_clean(final_output)
        validation = validate_output(chunk, final_output, mode)
        if validation.warnings and repair_enabled:
            repair_prompt = build_repair_prompt(chunk, final_output, validation.warnings, mode, manual_instruction, memory_prompt, dictionary_block)
            repaired = apply_dictionary_rules(post_clean(llm_client.generate(repair_prompt)), dictionary_rules)
            repaired = post_clean(repaired)
            repaired_validation = validate_output(chunk, repaired, mode)
            final_output = repaired
            validation = repaired_validation
        warnings.extend(validation.warnings)
        outputs.append(final_output)

    merged_output = apply_dictionary_rules(post_clean("\n\n".join(outputs)), dictionary_rules)
    merged_output = post_clean(merged_output)
    set_cell_text(workbook, sheet_name, row, output_col, merged_output)
    return RowResult(row=row, status="done", mode=mode, output=merged_output, warnings=warnings, chunks=len(chunks))
