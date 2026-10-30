"""Đọc và tiền xử lý ảnh tài liệu trước khi đưa vào OCR."""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

PREPROCESSING_MODES = (
    "original", "grayscale", "otsu", "adaptive", "clahe", "normalized", "deskew_normalized",
)


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


def _odd(value: int) -> int:
    """OpenCV yêu cầu kích thước kernel lẻ."""
    return value if value % 2 == 1 else value + 1


def normalize_illumination(gray: np.ndarray) -> np.ndarray:
    """Loại bóng đổ / sáng không đều bằng cách chia ảnh cho ước lượng nền.

    Closing (giãn rồi co) bằng kernel lớn hơn nét chữ sẽ xóa chữ và giữ lại nền;
    chia ảnh gốc cho nền đó làm nền phẳng về ~255 còn chữ vẫn tối.
    """
    kernel_size = _odd(max(15, min(gray.shape[:2]) // 25))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    background = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
    background = cv2.GaussianBlur(background, (0, 0), kernel_size / 3)
    return cv2.divide(gray, background, scale=255)


def rotate_keep_size(image: np.ndarray, angle: float, border_value: int = 255) -> np.ndarray:
    """Xoay quanh tâm ảnh, giữ nguyên kích thước canvas (góc dương = ngược chiều kim đồng hồ)."""
    height, width = image.shape[:2]
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
    return cv2.warpAffine(
        image, matrix, (width, height), flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT, borderValue=border_value,
    )


def estimate_skew_angle(gray: np.ndarray, max_angle: float = 12.0, step: float = 0.5) -> float:
    """Ước lượng góc cần xoay (độ) để các dòng chữ nằm ngang, bằng projection profile.

    Với mỗi góc thử: xoay ảnh nhị phân (chữ=255), cộng số pixel chữ theo từng hàng.
    Khi dòng chữ nằm ngang đúng, tổng theo hàng có đỉnh nhọn (hàng chữ rất nhiều pixel,
    khe giữa dòng gần 0) nên phương sai lớn nhất. Hòa điểm thì ưu tiên góc nhỏ hơn.
    """
    binary = cv2.threshold(normalize_illumination(gray), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    small = cv2.resize(255 - binary, None, fx=0.4, fy=0.4, interpolation=cv2.INTER_AREA)
    height, width = small.shape[:2]
    best_angle, best_score = 0.0, -1.0
    for angle in sorted(np.arange(-max_angle, max_angle + step, step), key=abs):
        matrix = cv2.getRotationMatrix2D((width / 2, height / 2), float(angle), 1.0)
        rotated = cv2.warpAffine(small, matrix, (width, height), flags=cv2.INTER_NEAREST)
        score = float(rotated.sum(axis=1).astype(np.float64).var())
        if score > best_score + 1e-9:
            best_angle, best_score = float(angle), score
    return best_angle


def map_bbox_to_original(bbox: list[int], angle: float, size: dict[str, int]) -> list[int]:
    """Đưa bbox [x, y, w, h] từ ảnh đã xoay `angle` độ về hệ tọa độ ảnh gốc (hộp bao 4 góc)."""
    width, height = size["width"], size["height"]
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
    inverse = cv2.invertAffineTransform(matrix)
    x, y, w, h = bbox
    corners = np.array([[x, y, 1], [x + w, y, 1], [x, y + h, 1], [x + w, y + h, 1]], dtype=float)
    moved = corners @ inverse.T
    x1, y1 = np.maximum(moved.min(axis=0), 0)
    x2, y2 = np.minimum(moved.max(axis=0), [width, height])
    return [int(x1), int(y1), int(max(x2 - x1, 0)), int(max(y2 - y1, 0))]


def preprocess_image(image: np.ndarray, mode: str = "original") -> np.ndarray:
    """Chỉ trả ảnh đã xử lý; dùng preprocess_with_info nếu cần góc xoay."""
    return preprocess_with_info(image, mode)[0]


def preprocess_with_info(image: np.ndarray, mode: str = "original") -> tuple[np.ndarray, dict]:
    """Tạo một biến thể ảnh để thử nghiệm OCR, không thay đổi chiều rộng/chiều cao.

    Các chế độ:
    - original: ảnh màu ban đầu.
    - grayscale: ảnh xám.
    - otsu: nhị phân hóa tự động bằng ngưỡng Otsu.
    - adaptive: nhị phân hóa thích nghi khi độ sáng không đồng đều.
    - clahe: tăng tương phản cục bộ trên ảnh xám.
    - normalized: ảnh xám đã loại bóng đổ (chia cho nền ước lượng), không nhị phân hóa.
    - deskew_normalized: chỉnh nghiêng rồi loại bóng đổ.

    Kích thước luôn giữ nguyên. Với deskew_normalized, tọa độ bbox nằm trong ảnh đã xoay;
    info["deskew_angle_degrees"] cho biết góc đã xoay để đưa bbox về hệ ảnh gốc.
    """
    if mode not in PREPROCESSING_MODES:
        raise ValueError(
            f"Chế độ không hợp lệ: {mode}. Chọn một trong: {', '.join(PREPROCESSING_MODES)}"
        )
    if image is None or image.size == 0:
        raise ValueError("Ảnh đầu vào rỗng.")
    info: dict = {}
    if mode == "original":
        return image.copy(), info

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image.copy()
    if mode == "grayscale":
        return gray, info
    if mode == "otsu":
        _, result = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return result, info
    if mode == "adaptive":
        # OpenCV cần block_size là số lẻ lớn hơn 1; giới hạn để dùng được với ảnh nhỏ.
        smallest_side = min(gray.shape[:2])
        block_size = min(31, smallest_side if smallest_side % 2 == 1 else smallest_side - 1)
        if block_size < 3:
            raise ValueError("Ảnh quá nhỏ để dùng nhị phân hóa thích nghi; cần cạnh nhỏ nhất >= 3 px.")
        result = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block_size, 11
        )
        return result, info
    if mode == "clahe":
        enhancer = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return enhancer.apply(gray), info
    if mode == "normalized":
        return normalize_illumination(gray), info
    if mode == "deskew_normalized":
        angle = estimate_skew_angle(gray)
        info["deskew_angle_degrees"] = angle
        return normalize_illumination(rotate_keep_size(gray, angle)), info
    # Nhánh này không thể được gọi nếu chế độ đã qua kiểm tra ở đầu hàm.
    raise AssertionError("Chế độ tiền xử lý chưa được triển khai.")


def image_size(image: np.ndarray) -> dict[str, int]:
    """Trả về chiều rộng và chiều cao của ảnh theo pixel."""
    height, width = image.shape[:2]
    return {"width": int(width), "height": int(height)}