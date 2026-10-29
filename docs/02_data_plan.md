# Milestone 1 và 2 — Kế hoạch dữ liệu

## 1. Chiến lược dữ liệu

Sử dụng ba nguồn, giữ tách biệt và ghi nguồn rõ ràng:

1. **Dữ liệu benchmark công khai:** dùng học OCR, bố cục và trích xuất thông tin. Mỗi bộ dữ liệu được đánh giá riêng, không gộp vào kết quả chính của tài liệu tiếng Việt.
2. **Tài liệu tiếng Việt giả lập:** hóa đơn và phiếu nhập tạo từ tên công ty, mặt hàng, ngày và số tiền hư cấu. Lưu nhãn JSON chuẩn và bbox dòng chữ nếu có.
3. **Tập test tổng hợp độc lập:** mẫu bố cục được tự thiết kế hoặc sinh riêng, không xuất hiện trong quá trình phát triển mô hình. Khóa tập này khi dùng để báo cáo cuối.

## 2. Các bộ dữ liệu công khai có thể tham khảo (phải xem điều khoản trước)

### SROIE

- Trang dự án/mirror tham khảo: <https://github.com/jsdnrs/ICDAR2019-SROIE>
- Phù hợp: OCR biên lai và trích xuất thông tin chính.
- Hạn chế: biên lai tiếng Anh, không phải hóa đơn tiếng Việt hay phiếu nhập kho. Không dùng kết quả trên bộ này để đại diện cho hiệu năng tiếng Việt.
- Trước khi dùng: kiểm tra điều khoản nguồn gốc và bản sao cụ thể; một mirror GitHub không tự động chứng minh quyền sử dụng mọi ảnh.

### CORD

- Kho dự án: <https://github.com/clovaai/cord>
- Phù hợp: thực hành phân tích biên lai, dòng hàng và cấu trúc trường.
- Hạn chế: dữ liệu chủ yếu là biên lai tiếng Hàn, nên chỉ dùng làm thử nghiệm bổ trợ.
- Trước khi dùng: kiểm tra phiên bản và giấy phép áp dụng cho ảnh/nhãn thực tế.

### MC-OCR — OCR biên lai tiếng Việt

- Trang thông tin: <https://www.rivf2021-mc-ocr.vietnlp.com/dataset>
- Phù hợp: văn bản biên lai tiếng Việt và annotation vùng chữ.
- Điều kiện: trang dữ liệu nêu yêu cầu đăng ký và ký thỏa thuận người dùng; mục đích sử dụng bị giới hạn. Chỉ dùng sau khi đáp ứng các điều kiện hiện hành.

## 3. Yêu cầu dữ liệu giả lập

- Chỉ dùng chi tiết hư cấu; không sao chép hóa đơn thật rồi thay một vài thông tin.
- Đa dạng mẫu: phông chữ, cỡ chữ, khoảng cách, bảng, xoay nhẹ, mờ/nhiễu và chất lượng ảnh.
- Mỗi mẫu có `source_type`, tên bộ dữ liệu, giấy phép/điều khoản, đường dẫn ảnh tương đối, split và `document_id` ổn định.
- Các biến thể của cùng mẫu gốc phải ở cùng split để tránh rò rỉ train/test.

## 4. Quy tắc chia tập

Dùng `train`, `validation` và `test`. Tập test cuối phải có nhóm bố cục chưa xuất hiện trong train. Không dùng test liên tục để chọn ngưỡng hoặc sửa quy tắc; nếu đã dùng test cho cải tiến, coi nó là validation và tạo test mới.

Với bộ dữ liệu khởi đầu nhỏ, không chia ngẫu nhiên rồi tuyên bố mô hình tổng quát tốt. Trước hết xây dựng quy trình gán nhãn và đánh giá; sau đó mới mở rộng số lượng và độ đa dạng template.

## 5. Trường trong manifest dữ liệu

Với mỗi bộ công khai, lưu:

- tên bộ dữ liệu và URL nguồn;
- phiên bản/ngày tải;
- URL giấy phép hoặc điều khoản truy cập;
- ngôn ngữ và loại tài liệu;
- số lượng mẫu được dùng;
- schema annotation và phiên bản script chuyển đổi;
- chính sách split và mẫu loại trừ;
- hạn chế về riêng tư, trích dẫn hoặc phân phối lại.

## 6. Quy tắc riêng tư

Không commit hóa đơn riêng tư, chứng từ thuế, mã định danh cá nhân, dữ liệu khách hàng/nhà cung cấp thật hoặc OCR phát sinh từ tài liệu riêng. Nếu thử nghiệm tài liệu thật cục bộ ở giai đoạn sau, hãy ẩn danh khi có thể và để trong `data/raw/user_provided/`, thư mục này được Git bỏ qua.
