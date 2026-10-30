"""Kiểm thử các biến thể tiền xử lý ảnh nếu nhóm phụ thuộc OCR đã được cài."""
from pathlib import Path

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2", reason="Cài nhóm phụ thuộc OCR để chạy test xử lý ảnh")
from documind.cv.preprocessing import PREPROCESSING_MODES, preprocess_image


@pytest.mark.parametrize("mode", PREPROCESSING_MODES)
def test_preprocessing_keeps_image_dimensions(mode: str):
    image = np.full((120, 240, 3), 255, dtype=np.uint8)
    cv2.putText(image, "DocuMind", (15, 65), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    processed = preprocess_image(image, mode)
    assert processed.shape[:2] == image.shape[:2]
    assert processed.size > 0


def test_invalid_preprocessing_mode_is_rejected():
    image = np.full((20, 20, 3), 255, dtype=np.uint8)
    with pytest.raises(ValueError):
        preprocess_image(image, "unknown")


# ----- Milestone 3.5: loại bóng đổ, chỉnh nghiêng, ánh xạ bbox -----
from documind.cv.preprocessing import (  # noqa: E402
    estimate_skew_angle,
    map_bbox_to_original,
    normalize_illumination,
    rotate_keep_size,
)


def _text_page(width: int = 700, height: int = 450) -> np.ndarray:
    page = np.full((height, width), 255, dtype=np.uint8)
    for index in range(8):
        cv2.putText(page, f"Dong {index} HD-2026 750000 VND", (40, 60 + index * 48),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, 0, 2)
    return page


def test_normalize_illumination_flattens_a_shadow_ramp():
    page = _text_page()
    ramp = np.linspace(0.45, 1.0, page.shape[1], dtype=np.float32)
    shadowed = (page * ramp[None, :]).astype(np.uint8)
    flat = normalize_illumination(shadowed)

    def edge_gap(image):  # chênh lệch độ sáng nền giữa mép trái và mép phải (vùng không có chữ)
        return abs(float(image[:, :15].mean()) - float(image[:, -15:].mean()))

    assert edge_gap(shadowed) > 80
    assert edge_gap(flat) < 15


def test_estimate_skew_angle_recovers_rotation():
    skewed = rotate_keep_size(_text_page(), 5.0)
    angle = estimate_skew_angle(skewed)
    assert abs(angle + 5.0) <= 1.0          # góc sửa ≈ ngược với góc đã làm nghiêng


def test_estimate_skew_angle_is_zero_for_blank_and_straight_pages():
    assert estimate_skew_angle(np.full((200, 300), 255, dtype=np.uint8)) == 0.0
    assert abs(estimate_skew_angle(_text_page())) <= 0.5


def test_map_bbox_to_original_encloses_the_original_box():
    size = {"width": 700, "height": 450}
    angle = -5.0                              # ảnh gốc nghiêng +5° được xoay -5° để chỉnh
    matrix = cv2.getRotationMatrix2D((350, 225), angle, 1.0)
    x, y, w, h = 100, 120, 200, 30
    corners = np.array([[x, y, 1], [x + w, y, 1], [x, y + h, 1], [x + w, y + h, 1]], dtype=float) @ matrix.T
    deskewed_box = [int(corners[:, 0].min()), int(corners[:, 1].min()),
                    int(corners[:, 0].max() - corners[:, 0].min()), int(corners[:, 1].max() - corners[:, 1].min())]
    mx, my, mw, mh = map_bbox_to_original(deskewed_box, angle, size)
    assert mx <= x + 3 and my <= y + 3 and mx + mw >= x + w - 3 and my + mh >= y + h - 3
    assert mw < w * 1.4 and mh < h * 4      # hộp bao lớn hơn một chút nhưng không phình quá mức