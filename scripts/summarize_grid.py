"""Tổng hợp CER trung bình theo (cấu hình OCR, chế độ tiền xử lý) x loại biến thể ảnh.

Chạy từ thư mục gốc dự án, mỗi thư mục là một cấu hình (ví dụ ngôn ngữ khác nhau):
    python scripts/summarize_grid.py data/processed/ocr_vie data/processed/ocr_vie_eng
In ra bảng Markdown để dán vào docs.
"""
from __future__ import annotations

import csv
import re
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

VARIANTS = ["clean", "rot5", "blur", "noise", "shadow", "jpeg"]
SUFFIX = re.compile(r"_(rot5|blur|noise|shadow|jpeg)$")


def main(dirs: list[str]) -> int:
    cells: dict[tuple[str, str], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for directory in dirs:
        path = Path(directory) / "evaluation.csv"
        if not path.is_file():
            print(f"[BỎ QUA] không có {path}")
            continue
        with path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                match = SUFFIX.search(row["document_id"])
                variant = match.group(1) if match else "clean"
                cells[(Path(directory).name, row["preprocessing_mode"])][variant].append(float(row["cer"]))
    if not cells:
        print("Không có dữ liệu để tổng hợp.")
        return 1

    print("| cấu hình | tiền xử lý | " + " | ".join(VARIANTS) + " | trung bình |")
    print("|---|---|" + "---:|" * (len(VARIANTS) + 1))
    for (config, mode), by_variant in sorted(cells.items()):
        values = [mean(by_variant[v]) * 100 if by_variant.get(v) else None for v in VARIANTS]
        present = [v for v in values if v is not None]
        text = [f"{v:.2f}%" if v is not None else "-" for v in values]
        print(f"| {config} | {mode} | " + " | ".join(text) + f" | {mean(present):.2f}% |")
    counts = {v: len(next(iter(cells.values())).get(v, [])) for v in VARIANTS}
    print("\nSố tài liệu mỗi ô (cấu hình đầu tiên):", counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))