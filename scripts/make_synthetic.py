"""Sinh hóa đơn / phiếu nhập kho giả lập, kèm biến thể ảnh xấu, và ghi nhãn JSONL khớp schema.

Chạy từ thư mục gốc dự án:
    python scripts/make_synthetic.py --count 6 --seed 42
Kết quả:
    data/raw/synthetic/<document_id>.png
    data/annotations/annotations.jsonl   (gồm 2 bản ghi mẫu ban đầu + bản ghi sinh ra)
"""
from __future__ import annotations

import argparse
import io
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

import cv2
import numpy as np
from jsonschema import Draft202012Validator, FormatChecker
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/document_annotation.schema.json"
EXAMPLE_PATH = ROOT / "data/annotations/annotations.example.jsonl"
IMAGE_DIR = ROOT / "data/raw/synthetic"

REGULAR_FONTS = [
    "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/tahoma.ttf", "C:/Windows/Fonts/segoeui.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/Library/Fonts/Arial.ttf",
]
BOLD_FONTS = [
    "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/tahomabd.ttf", "C:/Windows/Fonts/segoeuib.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/Library/Fonts/Arial Bold.ttf",
]

# Dữ liệu hư cấu. Không dùng thông tin của doanh nghiệp thật.
SUPPLIERS = ["Công ty TNHH Minh An", "Công ty CP Hoàng Long", "Công ty Văn Phòng ABC",
             "Cửa hàng Thanh Bình", "Công ty TNHH Thiên Phúc"]
BUYERS = ["Cửa hàng Sao Mai", "Công ty CP Đông Á", "Nhà sách Phương Nam", "Trường Tiểu học Hòa Bình"]
PEOPLE = ["Nhân viên giao hàng A", "Nhân viên giao hàng B", "Nhân viên kho B", "Nhân viên kho C"]
ITEMS = [("Giấy A4", "ram", 75000), ("Bút bi xanh", "chiếc", 5000), ("Vở 200 trang", "quyển", 18000),
         ("Kẹp giấy", "hộp", 12000), ("Mực in", "hộp", 320000), ("Bìa hồ sơ", "cái", 8000),
         ("Băng keo trong", "cuộn", 15000)]

WIDTH, HEIGHT = 1400, 1000


def pick_font(candidates: list[str], override: str | None, size: int) -> ImageFont.FreeTypeFont:
    for path in ([override] if override else []) + candidates:
        if path and Path(path).is_file():
            return ImageFont.truetype(path, size)
    raise SystemExit("Không tìm thấy font hỗ trợ tiếng Việt. Dùng --font <đường dẫn .ttf>.")


def build_lines(doc_type: str, number: int, rng: random.Random) -> tuple[list[str], dict]:
    """Trả về (các dòng chữ, bản ghi nhãn chưa có text_regions/source)."""
    day = (date(2026, 1, 1) + timedelta(days=rng.randint(0, 300))).isoformat()
    supplier = rng.choice(SUPPLIERS)
    rows = rng.sample(ITEMS, rng.randint(1, 4))
    items = []
    for i, (name, unit, price) in enumerate(rows, start=1):
        qty = rng.randint(1, 30)
        items.append({"line_number": i, "item_code": None, "description": name, "quantity": qty,
                      "unit": unit, "unit_price": price, "discount_amount": 0, "tax_rate": 0 if doc_type == "invoice" else None,
                      "line_total": qty * price if doc_type == "invoice" else None})
    subtotal = sum(it["quantity"] * it["unit_price"] for it in items)

    if doc_type == "invoice":
        buyer = rng.choice(BUYERS)
        doc_no = f"HD-2026-{number:03d}"
        lines = ["HOÁ ĐƠN BÁN HÀNG", f"Số hóa đơn: {doc_no}", f"Ngày lập: {day}", f"Nhà cung cấp: {supplier}",
                 f"Người mua: {buyer}", "STT | Tên hàng | SL | Đơn giá | Thành tiền"]
        lines += [f"{it['line_number']} | {it['description']} | {it['quantity']} | {it['unit_price']} | {it['line_total']}" for it in items]
        lines += [f"Cộng tiền hàng: {subtotal} VND", "Thuế: 0 VND", f"Tổng thanh toán: {subtotal} VND",
                  "DU LIEU GIA LAP - KHONG PHAI HOA DON THAT"]
        counterparty = {"role": "buyer", "name": buyer, "tax_id": None, "address": None}
        tax_total = 0
    else:
        warehouse = f"Kho số {rng.randint(1, 3)}"
        giver, receiver = rng.sample(PEOPLE[:2], 1)[0], rng.sample(PEOPLE[2:], 1)[0]
        doc_no = f"NK-2026-{number:03d}"
        lines = ["PHIẾU NHẬP KHO", f"Số phiếu: {doc_no}", f"Ngày nhập: {day}", f"Nhà cung cấp: {supplier}",
                 f"Kho nhận: {warehouse}", "STT | Tên hàng | SL | Đơn vị | Đơn giá"]
        lines += [f"{it['line_number']} | {it['description']} | {it['quantity']} | {it['unit']} | {it['unit_price']}" for it in items]
        lines += [f"Người giao: {giver}", f"Người nhận: {receiver}", "DU LIEU GIA LAP - KHONG PHAI PHIEU THAT"]
        counterparty = {"role": "warehouse_receiver", "name": warehouse, "tax_id": None, "address": None}
        tax_total = None

    record = {
        "schema_version": "1.0", "document_type": doc_type, "document_number": doc_no, "document_date": day,
        "supplier": {"name": supplier, "tax_id": None, "address": None}, "counterparty": counterparty,
        "items": items,
        "totals": {"subtotal": subtotal, "discount_total": 0, "tax_total": tax_total, "grand_total": subtotal, "currency": "VND"},
    }
    return lines, record


def render(lines: list[str], font_path: str | None, bold_path: str | None) -> tuple[Image.Image, list[dict]]:
    """Vẽ các dòng lên nền trắng và đo bbox [x, y, w, h] thật của từng dòng."""
    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)
    body, title = pick_font(REGULAR_FONTS, font_path, 26), pick_font(BOLD_FONTS, bold_path, 36)
    draw.rectangle([35, 35, WIDTH - 36, HEIGHT - 36], outline=(60, 60, 60), width=3)
    regions, y = [], 80
    for index, text in enumerate(lines):
        font = title if index == 0 else body
        if index == 0:
            width = draw.textlength(text, font=font)
            x = int((WIDTH - width) / 2)
        else:
            x = 70
        draw.text((x, y), text, font=font, fill=(17, 17, 17))
        left, top, right, bottom = draw.textbbox((x, y), text, font=font)
        regions.append({"text": text, "bbox": [left, top, right - left, bottom - top]})
        y += 62 if index == 0 else 48
    return image, regions


# ----- Biến thể ảnh xấu: giữ nguyên nhãn văn bản, chỉ cập nhật bbox khi hình học thay đổi -----
def rotate_variant(arr: np.ndarray, regions: list[dict], angle: float = 5.0):
    h, w = arr.shape[:2]
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    out = cv2.warpAffine(arr, matrix, (w, h), flags=cv2.INTER_CUBIC, borderValue=(255, 255, 255))
    new_regions = []
    for region in regions:
        x, y, bw, bh = region["bbox"]
        corners = np.array([[x, y, 1], [x + bw, y, 1], [x, y + bh, 1], [x + bw, y + bh, 1]], dtype=float)
        moved = corners @ matrix.T                     # tọa độ mới của 4 góc
        x1, y1 = np.maximum(moved.min(axis=0), 0)       # hộp bao nhỏ nhất quanh 4 góc
        x2, y2 = moved.max(axis=0)
        new_regions.append({"text": region["text"], "bbox": [int(x1), int(y1), int(x2 - x1), int(y2 - y1)]})
    return out, new_regions


def blur_variant(arr, regions):
    return cv2.GaussianBlur(arr, (0, 0), 1.6), regions


def noise_variant(arr, regions, rng: np.random.Generator):
    noisy = arr.astype(np.float32) + rng.normal(0, 18, arr.shape)
    return np.clip(noisy, 0, 255).astype(np.uint8), regions


def shadow_variant(arr, regions):
    ramp = np.linspace(0.45, 1.0, arr.shape[1], dtype=np.float32)      # tối bên trái, sáng bên phải
    return np.clip(arr * ramp[None, :, None], 0, 255).astype(np.uint8), regions


def jpeg_variant(arr, regions):
    buffer = io.BytesIO()
    Image.fromarray(arr).save(buffer, "JPEG", quality=25)
    return np.array(Image.open(buffer).convert("RGB")), regions


def main() -> int:
    parser = argparse.ArgumentParser(description="Sinh dữ liệu giả lập cho DocuMind")
    parser.add_argument("--count", type=int, default=6, help="số tài liệu gốc mỗi loại")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--font", help="đường dẫn .ttf hỗ trợ tiếng Việt")
    parser.add_argument("--bold-font", help="đường dẫn .ttf đậm cho tiêu đề")
    parser.add_argument("--no-degrade", action="store_true", help="không sinh biến thể ảnh xấu")
    parser.add_argument("--output", default=str(ROOT / "data/annotations/annotations.jsonl"))
    args = parser.parse_args()

    rng = random.Random(args.seed)
    np_rng = np.random.default_rng(args.seed)
    validator = Draft202012Validator(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")), format_checker=FormatChecker())
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    records: list[dict] = [json.loads(l) for l in EXAMPLE_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    prefixes = {"invoice": "synthetic_invoice", "stock_in_slip": "synthetic_stock_in_slip"}

    for doc_type, prefix in prefixes.items():
        for k in range(args.count):
            number = k + 2                                    # 001 đã dùng cho bản mẫu
            doc_id = f"{prefix}_{number:03d}"
            lines, base = build_lines(doc_type, number, rng)
            image, regions = render(lines, args.font, args.bold_font)
            # Mọi biến thể của cùng một tài liệu gốc phải nằm cùng split (tránh rò rỉ train/test).
            split = "train" if k % 10 < 7 else ("validation" if k % 10 < 9 else "test")
            arr = np.array(image)

            variants = {"": (arr, regions)}
            if not args.no_degrade:
                variants["rot5"] = rotate_variant(arr, regions)
                variants["blur"] = blur_variant(arr, regions)
                variants["noise"] = noise_variant(arr, regions, np_rng)
                variants["shadow"] = shadow_variant(arr, regions)
                variants["jpeg"] = jpeg_variant(arr, regions)

            for suffix, (img_arr, reg) in variants.items():
                vid = f"{doc_id}_{suffix}" if suffix else doc_id
                rel_path = f"data/raw/synthetic/{vid}.png"
                Image.fromarray(img_arr).save(ROOT / rel_path)
                record = {**base, "document_id": vid, "text_regions": reg,
                          "source": {"source_type": "synthetic", "dataset_name": "DocuMind generated synthetic",
                                     "license_or_terms": "Project-generated fictional example for learning",
                                     "image_path": rel_path, "split": split, "base_document_id": doc_id}}
                errors = list(validator.iter_errors(record))
                if errors:
                    print(f"[LỖI schema] {vid}: {errors[0].message}")
                    return 1
                records.append(record)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Đã ghi {len(records)} bản ghi vào {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())