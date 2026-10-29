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
