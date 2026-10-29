# Milestone 1 — Đặc tả bài toán

## 1. Bài toán

Xây dựng ứng dụng chạy cục bộ nhận đầu vào là ảnh **hóa đơn tiếng Việt** hoặc **phiếu nhập kho** và từng bước chuyển thành dữ liệu có cấu trúc, cho phép người dùng xem lại và chỉnh sửa. Hệ thống giúp giảm việc nhập liệu thủ công nhưng phải thể hiện sự không chắc chắn; không được âm thầm tự bịa giá trị còn thiếu.

## 2. Người dùng và mục đích sử dụng

- Nhân viên kho: số hóa phiếu nhập, thông tin nhà cung cấp và các dòng hàng.
- Nhân viên kế toán/hành chính: số hóa thông tin hóa đơn, đối tác, hàng hóa và tổng tiền.
- Người đánh giá dự án: đo chất lượng OCR và trích xuất trường trên tập nhãn đã cố định.

Đây là dự án học tập/minh họa, không phải hệ thống kế toán được chứng nhận. Người dùng vẫn cần xác nhận kết quả.

## 3. Hợp đồng đầu vào/đầu ra cho MVP

### Đầu vào

- Ảnh raster: PNG, JPG/JPEG, WEBP, TIFF.
- Hai lớp tài liệu: `invoice` và `stock_in_slip`.
- Dữ liệu công khai, dữ liệu giả lập do dự án tạo và mẫu riêng của người dùng được phân biệt bằng thông tin nguồn.

### Đầu ra chuẩn

- `document_id`, `document_type`, `document_number`, `document_date`.
- Thông tin nhà cung cấp và đối tác nhận/mua.
- `items`: tên/mã hàng, số lượng, đơn vị, đơn giá, chiết khấu, thuế suất và thành tiền.
- `totals`: tiền hàng, chiết khấu, thuế và tổng thanh toán.
- `source`: đường dẫn ảnh, nguồn dữ liệu, điều khoản/giấy phép và tập dữ liệu.
- `text_regions`: văn bản tham chiếu từng dòng và hộp `[x, y, width, height]` để đánh giá OCR.

Trường không có hoặc không đọc được có thể là `null`. Không được tự đoán giá trị rỗng, không đọc được hoặc không áp dụng.

## 4. Trong phạm vi và ngoài phạm vi

### Trong phạm vi

- Ảnh tài liệu, ưu tiên tiếng Việt.
- Phân loại hai loại tài liệu ở milestone sau.
- OCR và trích xuất trường.
- Trích xuất dòng hàng, kiểm tra phép tính, người dùng duyệt/sửa và xuất JSON/CSV.
- Đánh giá riêng từng thành phần và toàn pipeline.

### Ngoài phạm vi MVP đầu tiên

- Tích hợp phần mềm kế toán hoặc kiểm định thuế/pháp lý.
- Cam kết chính xác với mọi bố cục, chữ viết tay, ảnh nhiệt hoặc ảnh chất lượng rất thấp.
- Dịch vụ đám mây/API trả phí.
- Chấp nhận tự động dữ liệu tài chính mà không cần người xác nhận.
- PDF nhiều trang; chỉ xem xét sau khi pipeline ảnh đơn trang ổn định.

## 5. Tiêu chí thành công

Milestone 1 được chấp nhận khi:

1. Hai loại tài liệu và các trường cốt lõi được xác định.
2. Cả hai loại dùng được cùng schema nhưng vẫn giữ khác biệt về loại tài liệu.
3. Trường không biết có thể biểu diễn rõ ràng.
4. Mỗi mẫu truy được nguồn và điều khoản.
5. Dữ liệu đánh giá được tách khỏi dữ liệu train/validation.

Chỉ đặt mục tiêu số cho mô hình sau khi có baseline và tập test được gán nhãn; không tự đặt độ chính xác khi chưa đo.
