"""Kiểm tra Tesseract, pytesseract và các gói ngôn ngữ cần thiết."""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    """Chạy các bước kiểm tra và trả mã thoát khác 0 nếu có lỗi."""
    parser = argparse.ArgumentParser(description="Kiểm tra môi trường OCR của DocuMind")
    parser.add_argument("--tesseract-path", help="Đường dẫn đầy đủ đến tesseract.exe nếu chưa có trong PATH")
    args = parser.parse_args()

    try:
        import pytesseract
    except ImportError:
        print('[FAIL] Chưa có pytesseract. Chạy: python -m pip install -e ".[dev,ocr]"')
        return 1

    candidate = args.tesseract_path or os.getenv("DOCUMIND_TESSERACT_CMD")
    if candidate:
        pytesseract.pytesseract.tesseract_cmd = candidate
    executable = shutil.which(pytesseract.pytesseract.tesseract_cmd)
    if executable is None and Path(pytesseract.pytesseract.tesseract_cmd).is_file():
        executable = pytesseract.pytesseract.tesseract_cmd
    if executable is None:
        print("[FAIL] Không tìm thấy Tesseract OCR.")
        print("       Hãy cài Tesseract cho Windows hoặc truyền --tesseract-path đến tesseract.exe.")
        return 1
    print(f"[OK] Tesseract executable: {executable}")

    try:
        print(f"[OK] Tesseract version: {str(pytesseract.get_tesseract_version()).splitlines()[0]}")
        languages = sorted(pytesseract.get_languages(config=""))
    except Exception as exc:  # Hiển thị lỗi cài đặt/khởi chạy để người học tự xử lý.
        print(f"[FAIL] Không truy vấn được Tesseract: {exc}")
        return 1

    print("[INFO] Language packs: " + ", ".join(languages))
    missing = [language for language in ("vie", "eng") if language not in languages]
    if missing:
        print("[FAIL] Thiếu gói ngôn ngữ: " + ", ".join(missing))
        print("       Cần bổ sung dữ liệu `vie` và `eng` vào thư mục tessdata của Tesseract.")
        return 1
    print("[OK] Đã có cả vie và eng; có thể chạy baseline OCR tiếng Việt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
