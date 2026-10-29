"""Regression tests for the canonical annotation contract."""
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


def load_records():
    """Load the JSONL starter examples as Python dictionaries."""
    annotation_file = ROOT / "data/annotations/annotations.example.jsonl"
    return [json.loads(line) for line in annotation_file.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_example_annotations_match_schema():
    """Both starter documents must satisfy the shared JSON schema."""
    schema = json.loads((ROOT / "schemas/document_annotation.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    records = load_records()
    errors = [(record.get("document_id"), list(validator.iter_errors(record))) for record in records]
    assert all(not record_errors for _, record_errors in errors), errors


def test_examples_cover_both_document_types_and_existing_images():
    """Starter annotations must cover invoices and stock-in slips with local images."""
    records = load_records()
    assert {record["document_type"] for record in records} == {"invoice", "stock_in_slip"}
    for record in records:
        image_path = ROOT / record["source"]["image_path"]
        assert image_path.is_file(), f"Missing sample image: {image_path}"
