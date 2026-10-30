"""Chạy OCR cho một ảnh; có thể so sánh nhiều chế độ tiền xử lý."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from documind.cv.pipeline import run_ocr  # noqa: E402
from documind.cv.preprocessing import PREPROCESSING_MODES  # noqa: E402


def main() -> int:
    """Phân tích tham số và gọi pipeline OCR."""
    parser = argparse.ArgumentParser(description="Chạy OCR cục bộ cho tài liệu DocuMind")
    parser.add_argument("--image", required=True, help="Đường dẫn ảnh hóa đơn/phiếu nhập kho")
    parser.add_argument("--mode", choices=PREPROCESSING_MODES, default="original", help="Chế độ tiền xử lý ảnh")
    parser.add_argument("--all-modes", action="store_true", help="Chạy lần lượt mọi chế độ để so sánh")
    parser.add_argument("--document-id", help="Mã tài liệu; tự dò từ JSONL mẫu nếu bỏ trống")
    parser.add_argument("--language", default="vie", help="Mã gói ngôn ngữ Tesseract, mặc định vie+eng")
    parser.add_argument("--psm", type=int, default=6, help="Tesseract Page Segmentation Mode, mặc định 6")
    parser.add_argument("--tesseract-path", help="Đường dẫn đến tesseract.exe nếu chưa cấu hình PATH")
    parser.add_argument("--output-dir", default=str(ROOT / "data/processed/ocr"), help="Thư mục lưu JSON/TXT")
    parser.add_argument("--visualization-dir", default=str(ROOT / "data/processed/visualizations"), help="Thư mục lưu ảnh bbox")
    parser.add_argument("--no-visualization", action="store_true", help="Không tạo ảnh có khung bbox")
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.is_absolute():
        image_path = (Path.cwd() / image_path).resolve()
    modes = list(PREPROCESSING_MODES) if args.all_modes else [args.mode]
    try:
        # Tạo một engine và dùng lại cho mọi biến thể ảnh để giảm chi phí khởi tạo.
        from documind.cv.ocr_engine import TesseractOCR
        engine = TesseractOCR(executable_path=args.tesseract_path)
        print(f"Tesseract: {engine.version()}")
        print(f"Ngôn ngữ OCR: {args.language}; PSM: {args.psm}")
        for mode in modes:
            result = run_ocr(
                image_path=image_path,
                mode=mode,
                output_dir=args.output_dir,
                visualization_dir=args.visualization_dir,
                document_id=args.document_id,
                language=args.language,
                page_segmentation_mode=args.psm,
                engine=engine,
                create_visualization=not args.no_visualization,
            )
            print("\n" + "=" * 60)
            print(f"Tài liệu: {result['document_id']} | Chế độ: {mode}")
            print(f"Số dòng: {result['line_count']} | Thời gian: {result['elapsed_seconds']:.3f} giây")
            print("Văn bản OCR:")
            print(result["text"] or "[Không nhận diện được văn bản]")
            print(f"JSON: {result['output_json']}")
            print(f"TXT:  {result['output_text']}")
            if result.get("visualization_path"):
                print(f"Ảnh bbox: {result['visualization_path']}")
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"[LỖI] {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
