import os
from datetime import datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from omni_novel_editor.config import DEFAULT_BATCH_SIZE, DEFAULT_OUTPUT_HEADER
from omni_novel_editor.dictionary.rules import load_builtin_dictionary
from omni_novel_editor.excel.workbook import (
    column_options,
    find_or_create_output_column,
    first_blank_output_row,
    load_workbook_from_bytes,
    save_workbook_to_bytes,
    save_workbook_to_path,
    sheet_preview,
)
from omni_novel_editor.llm.gemini_client import GeminiClient
from omni_novel_editor.llm.model_router import select_model
from omni_novel_editor.memory.store import MemoryStore
from omni_novel_editor.processing.row_processor import process_row
from omni_novel_editor.storage.job_store import append_log, create_job_dir, write_json

load_dotenv()

st.set_page_config(page_title="Omni-Novel-Editor", layout="wide")


def init_state() -> None:
    defaults = {
        "workbook": None,
        "workbook_bytes": None,
        "filename": "",
        "sheet_name": "",
        "output_col": "",
        "job_dir": None,
        "logs": [],
        "errors": [],
        "completed_rows": [],
        "failed_rows": [],
        "memory": MemoryStore(),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def to_dataframe(preview: list[list[object]]) -> pd.DataFrame:
    max_len = max((len(row) for row in preview), default=0)
    normalized = [row + [None] * (max_len - len(row)) for row in preview]
    columns = [f"Cột {index + 1}" for index in range(max_len)]
    return pd.DataFrame(normalized, columns=columns)


def save_checkpoint(workbook, job_dir, state_payload: dict) -> bytes:
    output_bytes = save_workbook_to_bytes(workbook)
    if job_dir:
        partial_path = job_dir / "output_partial.xlsx"
        save_workbook_to_path(workbook, partial_path)
        write_json(job_dir / "state.json", state_payload)
    return output_bytes


init_state()

st.title("Omni-Novel-Editor")
st.caption("Tool local để hậu kiểm/dịch Excel tiểu thuyết ngôn tình sang bản Việt TTS-ready.")

with st.sidebar:
    st.header("Cấu hình Gemini")
    api_key = st.text_input(
        "Gemini API key",
        value=os.getenv("GEMINI_API_KEY", ""),
        type="password",
        help="Có thể nhập tại đây hoặc đặt GEMINI_API_KEY trong file .env.",
    )
    quality_mode = st.selectbox("Chế độ model", ["Nhanh / tiết kiệm", "Cân bằng", "Chất lượng cao"], index=1)
    model_name = select_model(quality_mode)
    st.caption(f"Model sẽ dùng: `{model_name}`")
    st.divider()
    batch_size = st.number_input("Số row mỗi batch", min_value=1, max_value=100, value=DEFAULT_BATCH_SIZE, step=1)
    max_chars = st.number_input("Kích thước chunk tối đa", min_value=2000, max_value=30000, value=12000, step=1000)
    repair_enabled = st.checkbox("Tự repair 1 lần nếu validator nghi hụt/lỗi", value=True)
    dictionary_rules = load_builtin_dictionary()
    strict_count = sum(1 for rule in dictionary_rules if not rule.is_ambiguous)
    ambiguous_count = sum(1 for rule in dictionary_rules if rule.is_ambiguous)
    st.divider()
    st.caption(f"Dictionary hậu kiểm mặc định: {strict_count} rule strict, {ambiguous_count} rule cần LLM chọn theo ngữ cảnh.")

uploaded_file = st.file_uploader("Upload file Excel .xlsx", type=["xlsx"])
if uploaded_file and uploaded_file.name != st.session_state.filename:
    data = uploaded_file.getvalue()
    st.session_state.workbook = load_workbook_from_bytes(data)
    st.session_state.workbook_bytes = data
    st.session_state.filename = uploaded_file.name
    st.session_state.sheet_name = st.session_state.workbook.sheetnames[0]
    st.session_state.output_col = ""
    st.session_state.job_dir = create_job_dir(uploaded_file.name)
    input_path = st.session_state.job_dir / "input.xlsx"
    input_path.write_bytes(data)
    st.session_state.logs = []
    st.session_state.errors = []
    st.session_state.completed_rows = []
    st.session_state.failed_rows = []
    st.success("Đã đọc file Excel. File gốc chỉ được lưu local trong thư mục data/jobs.")

if not st.session_state.workbook:
    st.info("Hãy upload file Excel để bắt đầu.")
    st.stop()

workbook = st.session_state.workbook
sheet_name = st.selectbox("Chọn sheet", workbook.sheetnames, index=workbook.sheetnames.index(st.session_state.sheet_name))
st.session_state.sheet_name = sheet_name
sheet = workbook[sheet_name]

st.subheader("Preview dữ liệu")
st.dataframe(to_dataframe(sheet_preview(workbook, sheet_name, rows=10)), use_container_width=True)
st.caption(f"Sheet hiện tại có {sheet.max_row} row và {sheet.max_column} cột.")

options = column_options(workbook, sheet_name)
letters = list(options.keys())

def default_letter(letter: str) -> int:
    return letters.index(letter) if letter in letters else 0

st.subheader("Mapping cột")
col1, col2, col3, col4 = st.columns(4)
with col1:
    chapter_index_col = st.selectbox("Cột số chapter", letters, index=default_letter("A"), format_func=lambda key: options[key])
with col2:
    chapter_title_col = st.selectbox("Cột title chapter", letters, index=default_letter("B"), format_func=lambda key: options[key])
with col3:
    chinese_col = st.selectbox("Cột source tiếng Trung", letters, index=default_letter("C"), format_func=lambda key: options[key])
with col4:
    vietnamese_col = st.selectbox("Cột bản Việt thô", letters, index=default_letter("D"), format_func=lambda key: options[key])

st.info("Logic source: nếu row có bản Việt thô thì app chỉ edit cột đó và không nhìn cột Trung. Nếu bản Việt thô rỗng/không chọn thì app mới dùng cột Trung để dịch.")
output_header = st.text_input("Tên cột output", value=DEFAULT_OUTPUT_HEADER)
if st.button("Tạo/tìm cột output") or not st.session_state.output_col:
    st.session_state.output_col = find_or_create_output_column(workbook, sheet_name, output_header)
    st.success(f"Cột output: {st.session_state.output_col}")

output_col = st.session_state.output_col or find_or_create_output_column(workbook, sheet_name, output_header)
st.session_state.output_col = output_col

st.subheader("Manual Instruction")
manual_instruction = st.text_area(
    "Instruction riêng của user — ưu tiên cao nhất nếu có",
    height=140,
    placeholder="Ví dụ: 陆景深 luôn dịch là Lục Cảnh Thâm. A luôn gọi B là chị. Văn phong mềm, cổ phong hơn...",
)

st.subheader("Điểm bắt đầu và batch")
first_blank = first_blank_output_row(workbook, sheet_name, output_col)
start_mode = st.radio("Chọn điểm bắt đầu", ["Row trống đầu tiên trong cột output", "Nhập row thủ công"], horizontal=True)
if start_mode == "Row trống đầu tiên trong cột output":
    start_row = first_blank
else:
    start_row = st.number_input("Start row", min_value=2, max_value=max(sheet.max_row, 2), value=min(first_blank, max(sheet.max_row, 2)), step=1)
end_row = min(int(start_row) + int(batch_size) - 1, sheet.max_row)
st.caption(f"Batch kế tiếp dự kiến xử lý row {int(start_row)} đến {end_row}.")

columns = {
    "chapter_index": chapter_index_col,
    "chapter_title": chapter_title_col,
    "chinese_source": chinese_col,
    "vietnamese_raw": vietnamese_col,
}

st.subheader("Xử lý")
run_col, download_col = st.columns([1, 1])
with run_col:
    run_batch = st.button("Chạy batch này", type="primary", disabled=not bool(api_key.strip()) or int(start_row) > sheet.max_row)
with download_col:
    current_bytes = save_workbook_to_bytes(workbook)
    st.download_button(
        "Download Excel hiện tại",
        data=current_bytes,
        file_name=f"{os.path.splitext(st.session_state.filename)[0]}_omni_partial.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

progress = st.progress(0)
status_box = st.empty()
error_box = st.empty()

if run_batch:
    client = GeminiClient(api_key=api_key, model=model_name)
    rows = list(range(int(start_row), end_row + 1))
    total = len(rows)
    state_base = {
        "filename": st.session_state.filename,
        "sheet_name": sheet_name,
        "output_col": output_col,
        "columns": columns,
        "manual_instruction": manual_instruction,
        "batch_size": batch_size,
        "updated_at": datetime.now().isoformat(),
        "builtin_dictionary_strict_rules": strict_count,
        "builtin_dictionary_ambiguous_rules": ambiguous_count,
    }
    for index, row in enumerate(rows, start=1):
        status_box.info(f"Đang xử lý row {row} / {end_row}...")
        try:
            result = process_row(
                workbook=workbook,
                sheet_name=sheet_name,
                row=row,
                columns=columns,
                output_col=output_col,
                llm_client=client,
                manual_instruction=manual_instruction,
                memory_prompt=st.session_state.memory.to_prompt(),
                max_chars=int(max_chars),
                repair_enabled=repair_enabled,
            )
            if result.status == "done":
                st.session_state.completed_rows.append(row)
                log_event = {"row": row, "status": "done", "mode": result.mode, "chunks": result.chunks, "warnings": result.warnings or []}
                if result.warnings:
                    st.warning(f"Row {row} có cảnh báo: {'; '.join(result.warnings)}")
            else:
                log_event = {"row": row, "status": result.status, "mode": result.mode, "error": result.error}
                st.warning(f"Row {row}: {result.error}")
        except Exception as exc:
            message = str(exc)
            st.session_state.failed_rows.append(row)
            st.session_state.errors.append({"row": row, "error": message})
            log_event = {"row": row, "status": "failed", "error": message}
            error_box.error(f"Row {row} bị lỗi: {message}. App đã lưu các row xử lý thành công trước đó.")
        append_log(st.session_state.job_dir / "logs.jsonl", log_event)
        state_payload = {
            **state_base,
            "last_processed_row": row,
            "completed_rows": st.session_state.completed_rows,
            "failed_rows": st.session_state.failed_rows,
            "errors": st.session_state.errors,
        }
        save_checkpoint(workbook, st.session_state.job_dir, state_payload)
        progress.progress(index / total)
    status_box.success("Batch đã kết thúc. Bạn có thể download Excel hiện tại hoặc chạy batch tiếp theo.")

if st.session_state.errors:
    st.subheader("Row bị lỗi")
    st.dataframe(pd.DataFrame(st.session_state.errors), use_container_width=True)

st.subheader("Tóm tắt session")
st.write(
    {
        "Cột output": output_col,
        "Rows hoàn thành": len(st.session_state.completed_rows),
        "Rows lỗi": len(st.session_state.failed_rows),
        "Thư mục job local": str(st.session_state.job_dir) if st.session_state.job_dir else "",
    }
)
