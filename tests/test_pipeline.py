from pathlib import Path
import importlib
import pytest

from app.models.entities import EmailMessage
from app.services.catalog import CatalogService
from app.services.excel import ExcelWriter
from app.services.llm import ExtractionEngine


def test_catalog_prompt_contains_aliases(tmp_path: Path):
    catalog = tmp_path / "catalog.csv"
    catalog.write_text("canonical_name,aliases\nProduct A,Alias A\n")
    service = CatalogService(catalog)
    prompt = service.to_prompt_block()
    assert "Product A" in prompt
    assert "Alias A" in prompt


def test_fallback_extraction_marks_possible_request(tmp_path: Path):
    catalog = tmp_path / "catalog.csv"
    catalog.write_text("canonical_name,aliases\nABC Dry Powder 6kg,6kg extinguisher\n")
    service = CatalogService(catalog)
    engine = ExtractionEngine(service)
    message = EmailMessage(
        message_id="1",
        subject="Need quote for extinguishers",
        sender="client@example.com",
        received_at="2026-03-22",
        body_text="Please send a quote for 4 units.",
    )
    result = engine._fallback_extract(message)
    assert result.is_product_request is True


@pytest.mark.skipif(importlib.util.find_spec('openpyxl') is None, reason='openpyxl not installed')
def test_excel_writer_appends_rows(tmp_path: Path):
    output = tmp_path / "out.xlsx"
    writer = ExcelWriter(output)
    message = EmailMessage(
        message_id="1",
        subject="Subject",
        sender="sender@example.com",
        received_at="2026-03-22",
        body_text="Body",
    )
    catalog = tmp_path / 'catalog.csv'
    catalog.write_text('canonical_name,aliases\nABC Dry Powder 6kg,6kg extinguisher\n')
    service = CatalogService(catalog)
    engine = ExtractionEngine(service)
    extraction = engine._normalize_payload(message, {
        'message_id': '1',
        'is_product_request': True,
        'confidence': 0.95,
        'customer_name': 'ACME',
        'customer_email': 'client@example.com',
        'freeform_notes': 'ok',
        'requested_lines': [{
            'canonical_name': 'ABC Dry Powder 6kg',
            'requested_name': '6kg extinguisher',
            'quantity': 4,
            'unit': 'pcs',
            'notes': '',
            'confidence': 0.98,
        }],
    })
    writer.append_result(message, extraction)
    assert output.exists()
