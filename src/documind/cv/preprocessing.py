"""Đọc và tiền xử lý ảnh tài liệu trước khi đưa vào OCR."""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

PREPROCESSING_MODES = ("original", "grayscale", "otsu", "adaptive", "clahe")


def load_image(image_path: str | Path) -> np.ndarray:
    """Đọc ảnh màu theo định dạng BGR; hỗ trợ đường dẫn Unicode trên Windows."""
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Không tìm thấy ảnh: {path}")

    # Dùng fromfile + imdecode để giảm lỗi khi đường dẫn chứa ký tự tiếng Việt.
    encoded = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Không đọc được ảnh hoặc định dạng không hỗ trợ: {path}")
    return image


def save_image(image: np.ndarray, image_path: str | Path) -> Path:
    """Lưu ảnh, kể cả khi đường dẫn có ký tự Unicode."""
    path = Path(image_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower() or ".png"
    success, encoded = cv2.imencode(suffix, image)
    if not success:
        raise ValueError(f"Không mã hóa được ảnh theo định dạng {suffix}: {path}")
    encoded.tofile(str(path))
    return path


def preprocess_image(image: np.ndarray, mode: str = "original") -> np.ndarray:
    """Tạo một biến thể ảnh để thử nghiệm OCR, không thay đổi chiều rộng/chiều cao.

    Các chế độ:
    - original: ảnh màu ban đầu.
    - grayscale: ảnh xám.
    - otsu: nhị phân hóa tự động bằng ngưỡng Otsu.
    - adaptive: nhị phân hóa thích nghi khi độ sáng không đồng đều.
    - clahe: tăng tương phản cục bộ trên ảnh xám.

    Giữ nguyên kích thước nhằm đảm bảo bbox OCR vẫn cùng hệ tọa độ với ảnh gốc.
    """
    if mode not in PREPROCESSING_MODES:
        raise ValueError(
            f"Chế độ không hợp lệ: {mode}. Chọn một trong: {', '.join(PREPROCESSING_MODES)}"
        )
    if image is None or image.size == 0:
        raise ValueError("Ảnh đầu vào rỗng.")
    if mode == "original":
        return image.copy()

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image.copy()
    if mode == "grayscale":
        return gray
    if mode == "otsu":
        _, result = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return result
    if mode == "adaptive":
        # OpenCV cần block_size là số lẻ lớn hơn 1; giới hạn để dùng được với ảnh nhỏ.
        smallest_side = min(gray.shape[:2])
        block_size = min(31, smallest_side if smallest_side % 2 == 1 else smallest_side - 1)
        if block_size < 3:
            raise ValueError("Ảnh quá nhỏ để dùng nhị phân hóa thích nghi; cần cạnh nhỏ nhất >= 3 px.")
        return cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block_size, 11
        )
    if mode == "clahe":
        enhancer = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return enhancer.apply(gray)
    # Nhánh này không thể được gọi nếu chế độ đã qua kiểm tra ở đầu hàm.
    raise AssertionError("Chế độ tiền xử lý chưa được triển khai.")


def image_size(image: np.ndarray) -> dict[str, int]:
    """Trả về chiều rộng và chiều cao của ảnh theo pixel."""
    height, width = image.shape[:2]
    return {"width": int(width), "height": int(height)}
