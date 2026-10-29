# Quy tắc chia tập dữ liệu

Các tập hợp được định danh là `train`, `validation` và `test`. Không chia các biến thể của cùng một tài liệu/template sang nhiều tập. Tập test cuối cần có nhóm template không dùng khi phát triển mô hình; khi đã dùng test để điều chỉnh pipeline, cần xem nó là validation và tạo một test mới.

Với hai ảnh giả lập khởi tạo, chưa có đủ mẫu để kết luận về năng lực tổng quát. Hiện dùng chúng để xác minh đường chạy và cách tính metric.
