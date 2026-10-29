# Nhãn tài liệu (JSONL)

`annotations.example.jsonl` chứa hai bản ghi minh họa, mỗi dòng là một JSON hoàn chỉnh. `text_regions` là văn bản tham chiếu để đo CER/WER và hộp chữ `[x, y, width, height]` theo pixel trong ảnh gốc.

Khi thêm dữ liệu, hãy giữ `document_id` ổn định và cập nhật thông tin `source`, giấy phép, đường dẫn ảnh và split. Không ghi thông tin riêng tư vào bộ dữ liệu mẫu hoặc kho Git.
