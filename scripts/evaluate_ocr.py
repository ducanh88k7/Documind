"""Tính CER/WER cho các kết quả OCR so với nhãn văn bản trong JSONL."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from documind.evaluation.ocr_metrics import cer, wer  # noqa: E402


def load_ground_truth(jsonl_path: Path) -> dict[str, str]:
    """Nối các vùng chữ gán nhãn theo thứ tự đã được lưu trong JSONL."""
    records: dict[str, str] = {}
    for line_number, raw_line in enumerate(jsonl_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSONL sai cú pháp ở dòng {line_number}: {exc}") from exc
        text_regions = record.get("text_regions", [])
        records[str(record["document_id"])] = " ".join(
            str(region.get("text", "")).strip() for region in text_regions if region.get("text", "").strip()
        )
    return records


def evaluate_directory(prediction_dir: Path, truth: dict[str, str]) -> list[dict[str, Any]]:
    """Đọc mọi JSON dự đoán hợp lệ trong thư mục và tính metric từng tài liệu/chế độ."""
    reports: list[dict[str, Any]] = []
    for path in sorted(prediction_dir.glob("*.json")):
        try:
            prediction = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(prediction, dict) or "lines" not in prediction or "document_id" not in prediction:
            continue
        document_id = str(prediction["document_id"])
        if document_id not in truth:
            print(f"[WARN] Không có ground truth cho {document_id}; bỏ qua {path.name}")
            continue
        predicted_text = " ".join(
            str(region.get("text", "")).strip()
            for region in prediction.get("lines", [])
            if str(region.get("text", "")).strip()
        )
        reference_text = truth[document_id]
        reports.append(
            {
                "document_id": document_id,
                "preprocessing_mode": prediction.get("preprocessing_mode", "unknown"),
                "line_count": prediction.get("line_count", len(prediction.get("lines", []))),
                "elapsed_seconds": prediction.get("elapsed_seconds"),
                "reference_characters": len(reference_text),
                "reference_words": len(reference_text.split()),
                "cer": round(cer(reference_text, predicted_text), 6),
                "wer": round(wer(reference_text, predicted_text), 6),
                "prediction_file": path.name,
            }
        )
    return reports


def main() -> int:
    """Xuất bảng metric để người học so sánh các chế độ tiền xử lý."""
    parser = argparse.ArgumentParser(description="Đánh giá OCR bằng CER và WER")
    parser.add_argument("--predictions", default=str(ROOT / "data/processed/ocr"), help="Thư mục JSON kết quả OCR")
    parser.add_argument("--ground-truth", default=str(ROOT / "data/annotations/annotations.example.jsonl"), help="File nhãn JSONL")
    parser.add_argument("--output", default=str(ROOT / "data/processed/ocr/evaluation.csv"), help="Đường dẫn CSV kết quả")
    args = parser.parse_args()

    prediction_dir = Path(args.predictions)
    truth_path = Path(args.ground_truth)
    if not prediction_dir.is_dir():
        print(f"[LỖI] Không tìm thấy thư mục dự đoán: {prediction_dir}")
        return 1
    if not truth_path.is_file():
        print(f"[LỖI] Không tìm thấy file ground truth: {truth_path}")
        return 1

    try:
        truth = load_ground_truth(truth_path)
        reports = evaluate_directory(prediction_dir, truth)
    except (OSError, ValueError, KeyError) as exc:
        print(f"[LỖI] {exc}")
        return 1
    if not reports:
        print("[LỖI] Chưa có kết quả OCR phù hợp. Hãy chạy scripts/run_ocr.py trước.")
        return 1

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(reports[0].keys())
    with output_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(reports)

    print("KẾT QUẢ ĐÁNH GIÁ OCR (CER/WER càng thấp càng tốt)")
    print("-" * 88)
    print(f"{'Tài liệu':34} {'Tiền xử lý':12} {'CER':>10} {'WER':>10} {'Giây':>10}")
    for row in reports:
        print(
            f"{row['document_id'][:34]:34} {row['preprocessing_mode']:12} "
            f"{row['cer'] * 100:9.2f}% {row['wer'] * 100:9.2f}% {row['elapsed_seconds']:10.3f}"
        )
    print("\nLưu bảng: " + str(output_path))
    print("Lưu ý: các ảnh mẫu còn ít; chỉ dùng để kiểm tra pipeline, chưa đủ để khẳng định chất lượng tổng quát.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
