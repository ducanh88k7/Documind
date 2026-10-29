# Milestone 2 — Thiết lập và vai trò từng tệp

## Vì sao các tệp này tồn tại?

- `pyproject.toml`: khai báo phiên bản Python hỗ trợ, metadata dự án và các nhóm thư viện cần thiết, giúp tái lập môi trường.
- `src/documind/__init__.py`: đánh dấu package Python có thể import và khai báo phiên bản.
- `schemas/document_annotation.schema.json`: quy định hợp đồng dữ liệu chung cho hóa đơn và phiếu nhập kho; phát hiện thiếu trường hoặc sai kiểu trước khi huấn luyện/đánh giá.
- `data/annotations/annotations.example.jsonl`: hai bản ghi giả lập mẫu, mỗi dòng là một đối tượng JSON riêng.
- `scripts/check_environment.py`: kiểm tra phiên bản Python, thư mục, thư viện, schema, nhãn mẫu và đường dẫn ảnh.
- `tests/test_annotation_schema.py`: kiểm thử để thay đổi sau này không âm thầm phá vỡ hợp đồng dữ liệu.
- `data/raw/public/`: nơi đặt dữ liệu công khai sau khi kiểm tra điều khoản; dữ liệu được tải về không mặc định đưa lên Git.
- `data/raw/synthetic/`: tài liệu hư cấu do dự án tạo.
- `data/raw/user_provided/`: mẫu cục bộ riêng của người dùng; bị Git bỏ qua.
- `data/splits/README.md`: chính sách tách biệt train/validation/test.
- `.gitignore`: ngăn commit môi trường ảo, bí mật, dữ liệu riêng, dataset tải về và kết quả sinh ra.
- `.env.example`: tài liệu cấu hình cục bộ tùy chọn, không chứa thông tin bí mật và không bắt buộc cho M1/M2.

## Chạy lệnh theo thứ tự

```powershell
py -0p
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python scripts/check_environment.py
python -m pytest
```

Nếu dùng Python 3.11, thay `-3.10` bằng `-3.11`. Trong PyCharm, mở **Settings → Project → Python Interpreter** và chọn `.venv\Scripts\python.exe`.

## Những phần chưa có ở Milestone 2

Chưa triển khai OCR, tiền xử lý ảnh, trích xuất NLP, huấn luyện mô hình, API hay giao diện. Các bước này được bổ sung sau khi hợp đồng dữ liệu và môi trường ban đầu được kiểm tra.
