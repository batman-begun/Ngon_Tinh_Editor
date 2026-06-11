# Omni-Novel-Editor

Omni-Novel-Editor là tool local dành cho nhóm user Việt Nam để xử lý file Excel tiểu thuyết ngôn tình. App đọc từng row/chapter, dùng Gemini API để dịch hoặc hậu kiểm, rồi xuất lại file Excel giữ nguyên dữ liệu cũ và thêm một cột output tiếng Việt final.

## Tính năng MVP

- Chạy local trên macOS bằng Streamlit.
- Input chỉ là file `.xlsx`.
- Output là file `.xlsx` mới/partial, giữ toàn bộ dữ liệu gốc và thêm cột `Omni Final Vietnamese`.
- Nếu row có cột bản Việt thô, app chỉ edit bản Việt thô và không nhìn cột tiếng Trung.
- Nếu bản Việt thô rỗng hoặc không chọn, app dùng cột tiếng Trung để dịch sang tiếng Việt rồi edit.
- Có ô `Manual Instruction`; nếu có nội dung, instruction này được đưa vào prompt với ưu tiên cao nhất.
- Batch mặc định 30 row/lần để user dễ kiểm soát tiến độ.
- Sau mỗi row hoàn thành, app tự lưu checkpoint và file `output_partial.xlsx` trong thư mục `data/jobs`.
- Nếu một row lỗi, app vẫn tiếp tục cố gắng giữ/export những row đã xử lý thành công.
- Có validator để cảnh báo output có nguy cơ bị hụt đoạn, còn Hán tự, hoặc còn foreign terms chưa Việt hóa.

## Cài đặt lần đầu

1. Giải nén package vào một thư mục bất kỳ.
2. Mở Terminal tại thư mục app.
3. Chạy:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Cách khác: double-click file `run_omni.command`. Lần đầu chạy script này sẽ tự tạo `.venv`, cài dependencies, rồi mở app Streamlit.

## Gemini API key

Bạn có 2 cách nhập key:

1. Nhập trực tiếp trong sidebar của app.
2. Copy `.env.example` thành `.env`, rồi điền:

```text
GEMINI_API_KEY=your_key_here
```

Không commit hoặc gửi file `.env` cho người khác.

## Workflow sử dụng

1. Upload file Excel `.xlsx`.
2. Chọn sheet cần xử lý.
3. Kiểm tra preview 10 row đầu.
4. Mapping các cột:
   - Cột số chapter.
   - Cột title chapter.
   - Cột source tiếng Trung.
   - Cột bản Việt thô.
5. Tạo/tìm cột output.
6. Nhập `Manual Instruction` nếu cần cố định tên nhân vật, xưng hô, hoặc văn phong.
7. Chọn điểm bắt đầu:
   - Row trống đầu tiên trong cột output.
   - Hoặc nhập row thủ công.
8. Chạy batch hiện tại.
9. Download Excel hiện tại bất cứ lúc nào sau khi có output.

## Quy tắc xử lý quan trọng

### Source priority

Nếu một row có bản Việt thô thì app dùng bản Việt thô làm source chính và không nhìn cột Trung. Cột Trung có thể không tồn tại.

Nếu bản Việt thô rỗng hoặc không được chọn, app mới dùng cột Trung để dịch.

### Manual Instruction

Manual Instruction là luật ưu tiên cao nhất trong prompt. Ví dụ:

```text
陆景深 luôn dịch là Lục Cảnh Thâm.
苏晚 luôn dịch là Tô Vãn.
A gọi B là chị trong mọi đoạn đối thoại.
Văn phong mềm mại, giàu cảm xúc, không hiện đại hóa quá mức.
```

### Error handling

Nếu một row bị lỗi Gemini/API/network/output, app sẽ:

- Báo lỗi trên UI.
- Ghi lỗi vào bảng `Row bị lỗi`.
- Lưu log trong `data/jobs/.../logs.jsonl`.
- Giữ nguyên các row đã xử lý thành công.
- Cho phép download file partial để session sau tiếp tục từ row trống đầu tiên.

## Thư mục local

Mỗi lần upload file, app tạo một job folder:

```text
data/jobs/YYYYMMDD_HHMMSS_filename_xxxxxxxx/
  input.xlsx
  output_partial.xlsx
  state.json
  logs.jsonl
```

Nếu app crash hoặc mạng lỗi, hãy mở lại app và upload file partial, rồi chọn tiếp tục từ row trống đầu tiên trong cột output.

## Lưu ý vận hành

- Nên test 3-5 row đầu trước khi chạy batch lớn.
- Batch mặc định 30 row là phù hợp với chapter ngôn tình thông thường.
- Nếu bị rate limit Gemini, giảm batch size hoặc tăng thời gian nghỉ giữa các lần chạy bằng cách chạy ít row hơn mỗi batch.
- Không đóng Terminal khi app đang xử lý.
