"""Pipeline tiền xử lý ảnh, chạy OCR và lưu kết quả có cấu trúc."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import cv2

from documind.cv.ocr_engine import TesseractOCR
from documind.cv.preprocessing import (
    PREPROCESSING_MODES,
    image_size,
    load_image,
    map_bbox_to_original,
    preprocess_with_info,
    save_image,
)

ROOT = Path(__file__).resolve().parents[3]
ANNOTATION_FILE = ROOT / "data/annotations/annotations.example.jsonl"


def resolve_document_id(image_path: str | Path, explicit_id: str | None = None) -> str:
    """Tìm document_id trong nhãn mẫu bằng đường dẫn ảnh; nếu không có thì dùng tên file."""
    path = Path(image_path).expanduser().resolve()
    if explicit_id:
        return explicit_id
    if ANNOTATION_FILE.is_file():
        import json as json_module
        for line in ANNOTATION_FILE.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json_module.loads(line)
            relative_path = record.get("source", {}).get("image_path")
            if not relative_path:
                continue
            candidate = (ROOT / relative_path).resolve()
            if candidate == path:
                return str(record["document_id"])
    return path.stem


def _project_relative_path(path: Path) -> str | None:
    """Trả đường dẫn tương đối khi ảnh nằm trong dự án, không ghi đường dẫn cá nhân vào JSON."""
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return None


def _draw_overlay(original: Any, lines: list[dict[str, Any]]) -> Any:
    """Vẽ các hộp OCR lên ảnh để tiện kiểm tra thủ công."""
    overlay = original.copy()
    for line in lines:
        x, y, width, height = line["bbox"]
        cv2.rectangle(overlay, (x, y), (x + width, y + height), (40, 180, 40), 2)
    return overlay


def run_ocr(
    image_path: str | Path,
    mode: str,
    output_dir: str | Path,
    visualization_dir: str | Path,
    document_id: str | None = None,
    language: str = "vie",
    page_segmentation_mode: int = 6,
    tesseract_path: str | Path | None = None,
    engine: TesseractOCR | None = None,
    create_visualization: bool = True,
) -> dict[str, Any]:
    """Chạy một cấu hình OCR và lưu JSON, TXT, ảnh đã xử lý và ảnh bbox (nếu bật)."""
    if mode not in PREPROCESSING_MODES:
        raise ValueError(f"mode phải thuộc: {', '.join(PREPROCESSING_MODES)}")
    source = Path(image_path).expanduser().resolve()
    original = load_image(source)
    prepared, info = preprocess_with_info(original, mode)
    doc_id = resolve_document_id(source, document_id)

    output_root = Path(output_dir)
    prepared_path = output_root.parent / "preprocessed" / f"{doc_id}_{mode}.png"
    save_image(prepared, prepared_path)

    ocr_engine = engine or TesseractOCR(executable_path=tesseract_path)
    started = time.perf_counter()
    lines = ocr_engine.recognize(
        prepared_path,
        language=language,
        page_segmentation_mode=page_segmentation_mode,
    )
    elapsed = time.perf_counter() - started
    size = image_size(original)

    angle = float(info.get("deskew_angle_degrees", 0.0))
    if angle:
        # OCR chạy trên ảnh đã xoay: giữ bbox gốc của OCR và đưa bbox chính về hệ ảnh gốc.
        for line in lines:
            line["bbox_processed"] = line["bbox"]
            line["bbox"] = map_bbox_to_original(line["bbox"], angle, size)

    result: dict[str, Any] = {
        "result_version": "1.0",
        "document_id": doc_id,
        "source_image_name": source.name,
        "source_image_path": _project_relative_path(source),
        "ocr_engine": "Tesseract OCR",
        "ocr_language": language,
        "page_segmentation_mode": page_segmentation_mode,
        "preprocessing_mode": mode,
        "deskew_angle_degrees": angle,
        "image_size": size,
        "elapsed_seconds": round(elapsed, 4),
        "line_count": len(lines),
        "text": "\n".join(line["text"] for line in lines),
        "lines": lines,
        "bbox_format": "[x, y, width, height] in pixels of original-size image",
    }

    output_root.mkdir(parents=True, exist_ok=True)
    json_path = output_root / f"{doc_id}_{mode}.json"
    txt_path = output_root / f"{doc_id}_{mode}.txt"
    txt_path.write_text(result["text"] + "\n", encoding="utf-8")
    result["output_json"] = str(json_path)
    result["output_text"] = str(txt_path)

    if create_visualization:
        visual_dir = Path(visualization_dir)
        visual_dir.mkdir(parents=True, exist_ok=True)
        overlay = _draw_overlay(original, lines)
        overlay_path = visual_dir / f"{doc_id}_{mode}_bbox.png"
        save_image(overlay, overlay_path)
        result["visualization_path"] = str(overlay_path)
    # Ghi JSON sau khi đã biết đầy đủ đường dẫn đầu ra, kể cả khi tắt visualization.
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result