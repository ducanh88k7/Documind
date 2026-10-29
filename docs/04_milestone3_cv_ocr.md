# Milestone 3 — Tiền xử lý ảnh và OCR

## 1. Mục tiêu

Tạo baseline OCR chạy trên CPU cho cả hóa đơn và phiếu nhập kho. Milestone này chỉ chuyển ảnh thành các dòng văn bản kèm vị trí và độ tin cậy; chưa phân loại trường như số hóa đơn, ngày lập, nhà cung cấp hay đơn giá. Việc hiểu ngữ nghĩa/NER sẽ thuộc milestone NLP sau.

## 2. Vì sao chọn Tesseract ở giai đoạn này?

Tesseract có thể chạy cục bộ; `pytesseract` chỉ là lớp kết nối Python, nên phải cài cả chương trình Tesseract và dữ liệu ngôn ngữ. Với tài liệu tiếng Việt, cần gói `vie`; thêm `eng` để nhận diện mã, chữ tiếng Anh và dãy số. Phiên bản OCR hiện tại dùng `--oem 3 --psm 6` mặc định và cho phép thay đổi PSM khi chạy lệnh.

Nguồn tham khảo:
- Hướng dẫn cài Tesseract: <https://github.com/tesseract-ocr/tessdoc/blob/main/Installation.md>
- Repository dữ liệu ngôn ngữ: <https://github.com/tesseract-ocr/tessdata>
- Trang so sánh OCR tiếng Việt (chỉ là một benchmark tham khảo, kết quả phụ thuộc loại ảnh): <https://nom-vn.nrl.ai/tasks/ocr>

## 3. Vai trò từng module và hàm

### `src/documind/cv/preprocessing.py`

- `load_image(image_path)`: đọc ảnh BGR, có xử lý đường dẫn Unicode trên Windows; báo lỗi nếu thiếu/không đọc được ảnh.
- `save_image(image, image_path)`: lưu ảnh qua OpenCV, hỗ trợ đường dẫn Unicode.
- `preprocess_image(image, mode)`: tạo ảnh gốc, ảnh xám, nhị phân Otsu, nhị phân thích nghi hoặc tăng tương phản CLAHE. Không thay đổi chiều rộng/chiều cao để bbox còn cùng tọa độ với ảnh gốc.
- `image_size(image)`: trả về chiều rộng và chiều cao ảnh theo pixel.
- `PREPROCESSING_MODES`: danh sách chế độ được hỗ trợ.

### `src/documind/cv/ocr_engine.py`

Lớp `TesseractOCR`:

- `__init__(executable_path=None)`: nạp `pytesseract`, và tùy chọn cấu hình đường dẫn `tesseract.exe`.
- `version()`: trả phiên bản Tesseract.
- `languages()`: trả các gói ngôn ngữ nhìn thấy được.
- `recognize(image_path, language="vie+eng", page_segmentation_mode=6)`: lấy kết quả từng từ từ Tesseract, gom các từ theo dòng và trả danh sách gồm `text`, `confidence` và `bbox`.

Confidence ở đây là điểm do Tesseract trả về rồi chia cho 100; nó **không** được đảm bảo là xác suất đúng đã hiệu chuẩn.

### `src/documind/cv/pipeline.py`

- `resolve_document_id(image_path, explicit_id=None)`: dò `document_id` từ nhãn mẫu nếu đường dẫn ảnh khớp; nếu không thì dùng tên file hoặc mã truyền vào.
- `_project_relative_path(path)`: trả đường dẫn tương đối nếu ảnh nằm trong dự án, tránh ghi đường dẫn người dùng vào JSON nếu ảnh ở ngoài dự án.
- `_draw_overlay(original, lines)`: vẽ bbox lên ảnh gốc để kiểm tra bằng mắt.
- `run_ocr(...)`: phối hợp đọc ảnh, tiền xử lý, chạy engine và lưu JSON/TXT/ảnh minh họa.

### `src/documind/evaluation/ocr_metrics.py`

- `normalize_text(text, case_insensitive=True)`: chuẩn hóa Unicode NFC, chữ hoa/thường và khoảng trắng; không xóa dấu tiếng Việt.
- `edit_distance(reference, prediction)`: tính khoảng cách Levenshtein.
- `error_rate(reference, prediction, unit)`: tính tỷ lệ lỗi theo ký tự hoặc từ.
- `cer(reference, prediction)`: Character Error Rate.
- `wer(reference, prediction)`: Word Error Rate.

### Các script

- `scripts/check_ocr_environment.py`: kiểm tra package Python, file thực thi Tesseract và gói ngôn ngữ `vie`, `eng`.
- `scripts/run_ocr.py`: CLI chạy một ảnh hoặc toàn bộ chế độ tiền xử lý.
- `scripts/evaluate_ocr.py`: so sánh mọi JSON OCR hợp lệ trong thư mục với `text_regions` của nhãn và xuất CSV.

## 4. Cài thư viện Python và Tesseract

Sau khi kích hoạt `.venv`:

```powershell
python -m pip install -e ".[dev,ocr]"
```

Cài Tesseract OCR cho Windows theo hướng dẫn upstream. Xác minh `tesseract.exe` nằm trong PATH hoặc chuẩn bị đường dẫn đầy đủ. Trong thư mục `tessdata`, cần có `vie.traineddata` và `eng.traineddata`.

```powershell
python scripts/check_ocr_environment.py
```

Nếu Tesseract không nằm trong PATH:

```powershell
python scripts/check_ocr_environment.py --tesseract-path "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

## 5. Chạy OCR

Chạy một chế độ làm mốc:

```powershell
python scripts/run_ocr.py --image data/raw/synthetic/sample_invoice_001.png --mode original
```

So sánh toàn bộ chế độ trên hóa đơn:

```powershell
python scripts/run_ocr.py --image data/raw/synthetic/sample_invoice_001.png --all-modes
```

Chạy trên phiếu nhập kho:

```powershell
python scripts/run_ocr.py --image data/raw/synthetic/sample_stock_in_slip_001.png --all-modes
```

Có thể chỉ định ngôn ngữ, PSM và đường dẫn Tesseract:

```powershell
python scripts/run_ocr.py --image data/raw/synthetic/sample_invoice_001.png --mode otsu --language vie+eng --psm 6 --tesseract-path "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### Ý nghĩa năm chế độ

| Chế độ | Phép biến đổi | Giả thuyết cần kiểm tra |
|---|---|---|
| `original` | Giữ ảnh màu | Là mốc so sánh |
| `grayscale` | Chuyển sang ảnh xám | Màu sắc không đóng góp thông tin chữ |
| `otsu` | Nhị phân hóa bằng ngưỡng toàn cục | Nền tương đối đồng đều |
| `adaptive` | Nhị phân hóa theo vùng nhỏ | Ánh sáng không đồng đều |
| `clahe` | Tăng tương phản cục bộ | Chữ nhạt có thể dễ đọc hơn; nhiễu cũng có thể tăng |

Không mặc định rằng ảnh xử lý nhiều hơn sẽ tạo OCR tốt hơn. Dùng CER/WER và kiểm tra kết quả trực quan để chọn.

## 6. Đầu ra

- `data/processed/preprocessed/`: ảnh biến đổi theo chế độ.
- `data/processed/ocr/<document_id>_<mode>.json`: cấu hình, nội dung, confidence và bbox từng dòng.
- `data/processed/ocr/<document_id>_<mode>.txt`: văn bản dễ đọc.
- `data/processed/visualizations/`: ảnh với bbox được vẽ.

Một dòng JSON OCR có dạng khái quát:

```json
{
  "text": "Số hóa đơn: HD-2026-001",
  "confidence": 0.94,
  "bbox": [68, 135, 335, 30]
}
```

Số liệu trên chỉ là ví dụ minh họa. `bbox` theo định dạng `[x, y, width, height]`, gốc tọa độ ở góc trên-trái.

## 7. Đánh giá

Sau khi đã tạo các kết quả OCR cho hai ảnh:

```powershell
python scripts/evaluate_ocr.py
```

Bảng CSV so sánh CER/WER theo tài liệu và chế độ. CER/WER thấp hơn thể hiện ít lỗi hơn trên tập tham chiếu. Script chuyển chữ về Unicode NFC, không phân biệt hoa/thường, gộp khoảng trắng và giữ nguyên dấu tiếng Việt.

Vì hiện chỉ có hai ảnh mẫu, metric còn rất thiếu tính đại diện. Mục tiêu lúc này là xác nhận đường chạy, học cách đọc lỗi và xác định chế độ nào phù hợp cho hai ảnh giả lập. Không dùng kết quả nhỏ này để kết luận engine nào tốt nhất cho mọi tài liệu.

### Kết quả kiểm thử tham chiếu trong môi trường tạo gói

Tesseract 5.5.0 đã chạy thành công trên hai ảnh giả lập trong môi trường tạo gói. Đây là số đo kiểm tra đường chạy, không phải cam kết kết quả trên máy của bạn.

| Tài liệu | Chế độ | CER | WER |
|---|---|---:|---:|
| Hóa đơn mẫu | `original` | 0,00% | 0,00% |
| Hóa đơn mẫu | `grayscale` | 0,00% | 0,00% |
| Hóa đơn mẫu | `otsu` | 3,87% | 14,29% |
| Hóa đơn mẫu | `adaptive` | 1,94% | 5,71% |
| Hóa đơn mẫu | `clahe` | 1,94% | 5,71% |
| Phiếu nhập kho mẫu | `original` | 0,00% | 0,00% |
| Phiếu nhập kho mẫu | `grayscale` | 0,00% | 0,00% |
| Phiếu nhập kho mẫu | `otsu` | 0,00% | 0,00% |
| Phiếu nhập kho mẫu | `adaptive` | 0,31% | 1,28% |
| Phiếu nhập kho mẫu | `clahe` | 0,00% | 0,00% |

Quan sát: với hai ảnh sạch này, ảnh gốc/ảnh xám đã rất tốt; nhị phân hóa Otsu thậm chí làm mất dấu ở một số dòng hóa đơn. Đây là ví dụ vì sao không nên mặc định tiền xử lý mạnh hơn là tốt hơn.

## 8. Checklist nghiệm thu Milestone 3

- [ ] Tesseract chạy được từ môi trường dự án và thấy được `vie`, `eng`.
- [ ] Chạy OCR trên hóa đơn và phiếu nhập kho bằng CPU.
- [ ] JSON/TXT và ảnh bbox được tạo ra.
- [ ] Năm biến thể tiền xử lý không đổi kích thước ảnh.
- [ ] Lệnh đánh giá tạo CSV CER/WER có các kết quả mong đợi.
- [ ] Đã mở ảnh bbox và kiểm tra văn bản nhận diện, ghi chú ít nhất ba loại lỗi thực tế.
- [ ] Chưa chuyển sang NLP cho đến khi kiểm tra xong các kết quả này.
