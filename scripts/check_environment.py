"""Kiểm tra môi trường cục bộ và dữ liệu khởi tạo của Milestone 1/2."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIN_PYTHON = (3, 10)
MAX_PYTHON = (3, 14)  # exclusive
REQUIRED_DIRS = [
    "data/annotations",
    "data/raw/public",
    "data/raw/synthetic",
    "data/raw/user_provided",
    "data/processed",
    "data/splits",
    "schemas",
    "tests",
]
REQUIRED_MODULES = ["PIL", "jsonschema", "pytest"]


def check_python() -> bool:
    """Trả về True nếu phiên bản Python nằm trong phạm vi dự án hỗ trợ."""
    current = sys.version_info[:2]
    ok = MIN_PYTHON <= current < MAX_PYTHON
    print(f"{'[OK]' if ok else '[FAIL]'} Python: {sys.version.split()[0]} (hỗ trợ: >=3.10,<3.14)")
    return ok


def check_directories() -> bool:
    """Kiểm tra các thư mục dữ liệu và mã nguồn cần thiết ở Milestone 2."""
    missing = [relative for relative in REQUIRED_DIRS if not (ROOT / relative).is_dir()]
    if missing:
        print("[FAIL] Thiếu thư mục: " + ", ".join(missing))
        return False
    print(f"[OK] Các thư mục bắt buộc đã tồn tại (đã kiểm tra {len(REQUIRED_DIRS)} thư mục)")
    return True


def check_modules() -> bool:
    """Kiểm tra các thư viện cần cho việc xác thực schema và chạy test."""
    missing = [name for name in REQUIRED_MODULES if importlib.util.find_spec(name) is None]
    if missing:
        print("[FAIL] Thiếu thư viện Python: " + ", ".join(missing))
        print('       Cài bằng lệnh: python -m pip install -e ".[dev]"')
        return False
    print("[OK] Có thể import các gói bắt buộc: " + ", ".join(REQUIRED_MODULES))
    return True


def check_annotations() -> bool:
    """Đối chiếu từng bản ghi JSONL với schema và kiểm tra đường dẫn ảnh."""
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError:
        print("[FAIL] Chưa cài jsonschema nên không thể kiểm tra nhãn")
        return False

    schema_path = ROOT / "schemas/document_annotation.schema.json"
    annotations_path = ROOT / "data/annotations/annotations.example.jsonl"
    if not schema_path.is_file() or not annotations_path.is_file():
        print("[FAIL] Thiếu schema hoặc file nhãn mẫu")
        return False

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    records = []
    errors = []
    for line_no, line in enumerate(annotations_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"dòng {line_no}: JSON không hợp lệ ({exc})")
            continue
        records.append(record)
        for error in validator.iter_errors(record):
            path = ".".join(str(part) for part in error.absolute_path) or "<root>"
            errors.append(f"dòng {line_no}, {path}: {error.message}")
        image_path = record.get("source", {}).get("image_path", "")
        if image_path and not (ROOT / image_path).is_file():
            errors.append(f"dòng {line_no}: không tìm thấy ảnh được tham chiếu: {image_path}")

    doc_types = {record.get("document_type") for record in records}
    if not {"invoice", "stock_in_slip"}.issubset(doc_types):
        errors.append("nhãn ví dụ phải có cả invoice và stock_in_slip")

    if errors:
        print("[FAIL] Lỗi kiểm tra nhãn/schema:")
        for err in errors:
            print("       - " + err)
        return False
    print(f"[OK] {len(records)} bản ghi JSONL khớp schema và trỏ đến ảnh đang tồn tại")
    return True


def check_public_data_notice() -> None:
    """Thông báo nếu chưa thêm dữ liệu công khai; đây là điều bình thường lúc khởi tạo."""
    public_dir = ROOT / "data/raw/public"
    files = [p for p in public_dir.rglob("*") if p.is_file() and p.name not in {"README.md", ".gitkeep", "datasets_manifest.csv"}]
    if files:
        print(f"[INFO] Tìm thấy {len(files)} tệp dữ liệu công khai (cần kiểm tra manifest giấy phép trước khi dùng)")
    else:
        print("[INFO] Chưa thêm bộ dữ liệu công khai; điều này bình thường ở Milestone 2")


def main() -> int:
    """Chạy mọi kiểm tra Milestone 2 và trả về mã thoát cho hệ điều hành."""
    print("DocuMind — kiểm tra môi trường Milestone 1/2")
    checks = [check_python(), check_directories(), check_modules(), check_annotations()]
    check_public_data_notice()
    if all(checks):
        print("\nKẾT QUẢ: ĐẠT — môi trường và dữ liệu khởi tạo sẵn sàng để kiểm tra.")
        return 0
    print("\nKẾT QUẢ: CHƯA ĐẠT — hãy sửa các mục [FAIL] trước khi tiếp tục.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
