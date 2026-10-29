"""Các metric cơ bản để đánh giá OCR bằng dữ liệu tham chiếu."""
from __future__ import annotations

import unicodedata


def normalize_text(text: str, case_insensitive: bool = True) -> str:
    """Chuẩn hóa Unicode NFC và khoảng trắng; không loại bỏ dấu tiếng Việt."""
    normalized = unicodedata.normalize("NFC", text)
    if case_insensitive:
        normalized = normalized.casefold()
    return " ".join(normalized.split())


def edit_distance(reference: list[str] | str, prediction: list[str] | str) -> int:
    """Tính Levenshtein distance bằng bộ nhớ O(min(m, n))."""
    # Nếu đầu vào là chuỗi, so sánh theo ký tự; nếu là list, so sánh theo token.
    ref_tokens = list(reference) if isinstance(reference, str) else reference
    pred_tokens = list(prediction) if isinstance(prediction, str) else prediction
    if len(ref_tokens) < len(pred_tokens):
        ref_tokens, pred_tokens = pred_tokens, ref_tokens
    previous = list(range(len(pred_tokens) + 1))
    for i, ref_token in enumerate(ref_tokens, start=1):
        current = [i]
        for j, pred_token in enumerate(pred_tokens, start=1):
            substitution_cost = 0 if ref_token == pred_token else 1
            current.append(
                min(
                    previous[j] + 1,             # xóa một token của tham chiếu
                    current[j - 1] + 1,           # chèn một token vào kết quả dự đoán
                    previous[j - 1] + substitution_cost,
                )
            )
        previous = current
    return previous[-1]


def error_rate(reference: str, prediction: str, unit: str = "char") -> float:
    """Tính CER hoặc WER; kết quả là tỷ lệ, ví dụ 0.12 nghĩa là 12%."""
    ref = normalize_text(reference)
    pred = normalize_text(prediction)
    if unit == "char":
        ref_tokens: list[str] | str = ref
        pred_tokens: list[str] | str = pred
    elif unit == "word":
        ref_tokens = ref.split() if ref else []
        pred_tokens = pred.split() if pred else []
    else:
        raise ValueError("unit phải là 'char' hoặc 'word'.")

    denominator = len(ref_tokens)
    if denominator == 0:
        return 0.0 if len(pred_tokens) == 0 else 1.0
    return edit_distance(ref_tokens, pred_tokens) / denominator


def cer(reference: str, prediction: str) -> float:
    """Character Error Rate: sai khác theo ký tự chia số ký tự tham chiếu."""
    return error_rate(reference, prediction, unit="char")


def wer(reference: str, prediction: str) -> float:
    """Word Error Rate: sai khác theo từ chia số từ tham chiếu."""
    return error_rate(reference, prediction, unit="word")
