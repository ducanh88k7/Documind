"""Kiểm thử metric OCR mà không cần cài engine Tesseract."""
from documind.evaluation.ocr_metrics import cer, edit_distance, normalize_text, wer


def test_normalize_keeps_vietnamese_diacritics_and_normalizes_unicode():
    assert normalize_text("  HOÁ   ĐƠN ") == "hoá đơn"
    assert normalize_text("a\u0301") == normalize_text("á")
    assert normalize_text("ma", case_insensitive=False) != normalize_text("má", case_insensitive=False)


def test_edit_distance_for_strings_and_tokens():
    assert edit_distance("kitten", "sitting") == 3
    assert edit_distance(["a", "b"], ["a", "c", "b"]) == 1


def test_cer_and_wer_return_zero_for_exact_match():
    assert cer("Hóa đơn số 01", "HÓA   ĐƠN số 01") == 0.0
    assert wer("Hóa đơn số 01", "HÓA   ĐƠN số 01") == 0.0


def test_error_rates_detect_substitution_and_empty_reference():
    assert cer("abc", "adc") == 1 / 3
    assert wer("một hai", "một ba") == 0.5
    assert cer("", "text") == 1.0
    assert wer("", "") == 0.0
