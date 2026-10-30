"""Lớp bao OCR sử dụng Tesseract và gói ngôn ngữ tiếng Việt."""
from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


class TesseractOCR:
    """Nhận diện chữ và gom các từ thành từng dòng.

    Yêu cầu: đã cài gói Python pytesseract và chương trình Tesseract OCR của hệ điều hành.
    Gói ngôn ngữ `vie` và `eng` cần có sẵn nếu dùng cấu hình mặc định `vie+eng`.
    """

    def __init__(self, executable_path: str | Path | None = None) -> None:
        try:
            import pytesseract
        except ImportError as exc:
            raise RuntimeError(
                'Thiếu pytesseract. Hãy cài bằng: python -m pip install -e ".[dev,ocr]"'
            ) from exc

        # Cho phép cấu hình Tesseract bằng tham số hoặc biến môi trường máy cục bộ.
        configured_path = executable_path or os.getenv("DOCUMIND_TESSERACT_CMD")
        if configured_path:
            pytesseract.pytesseract.tesseract_cmd = str(configured_path)
        self._pytesseract = pytesseract

    def version(self) -> str:
        """Trả về phiên bản Tesseract đang được gọi."""
        return str(self._pytesseract.get_tesseract_version()).splitlines()[0]

    def languages(self) -> list[str]:
        """Liệt kê các gói ngôn ngữ mà Tesseract nhìn thấy."""
        return sorted(self._pytesseract.get_languages(config=""))

    def recognize(
        self,
        image_path: str | Path,
        language: str = "vie",
        page_segmentation_mode: int = 6,
    ) -> list[dict[str, Any]]:
        """Trả kết quả theo từng dòng gồm nội dung, confidence và bbox [x, y, w, h]."""
        path = Path(image_path)
        if not path.is_file():
            raise FileNotFoundError(f"Không tìm thấy ảnh OCR: {path}")
        if not language.strip():
            raise ValueError("Tham số ngôn ngữ OCR không được để trống.")
        if page_segmentation_mode not in range(0, 14):
            raise ValueError("PSM phải là số nguyên từ 0 đến 13.")

        try:
            data = self._pytesseract.image_to_data(
                str(path),
                lang=language,
                config=f"--oem 3 --psm {page_segmentation_mode}",
                output_type=self._pytesseract.Output.DICT,
            )
        except self._pytesseract.TesseractNotFoundError as exc:
            raise RuntimeError(
                "Không tìm thấy Tesseract. Hãy cài Tesseract OCR và thêm vào PATH, "
                "hoặc truyền --tesseract-path đến tesseract.exe."
            ) from exc
        except self._pytesseract.TesseractError as exc:
            raise RuntimeError(
                f"Tesseract không xử lý được ảnh. Kiểm tra gói ngôn ngữ '{language}'. Chi tiết: {exc}"
            ) from exc

        grouped: dict[tuple[int, int, int, int], list[dict[str, Any]]] = defaultdict(list)
        count = len(data.get("text", []))
        for idx in range(count):
            text = str(data["text"][idx]).strip()
            try:
                confidence = float(data["conf"][idx])
            except (TypeError, ValueError):
                confidence = -1.0
            if not text or confidence < 0:
                continue

            key = (
                int(data["page_num"][idx]),
                int(data["block_num"][idx]),
                int(data["par_num"][idx]),
                int(data["line_num"][idx]),
            )
            grouped[key].append(
                {
                    "text": text,
                    "confidence": confidence,
                    "left": int(data["left"][idx]),
                    "top": int(data["top"][idx]),
                    "width": int(data["width"][idx]),
                    "height": int(data["height"][idx]),
                }
            )

        lines: list[dict[str, Any]] = []
        # Tesseract đã trả các từ theo thứ tự đọc; giữ thứ tự lần xuất hiện của từng dòng.
        for words in grouped.values():
            x1 = min(word["left"] for word in words)
            y1 = min(word["top"] for word in words)
            x2 = max(word["left"] + word["width"] for word in words)
            y2 = max(word["top"] + word["height"] for word in words)
            lines.append(
                {
                    "text": " ".join(word["text"] for word in words),
                    "confidence": round(mean(word["confidence"] for word in words) / 100.0, 4),
                    "bbox": [x1, y1, max(0, x2 - x1), max(0, y2 - y1)],
                }
            )
        return lines
