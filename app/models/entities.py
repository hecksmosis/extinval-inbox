from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AttachmentPayload:
    filename: str
    content_type: str
    path: Path
    extracted_text: str = ""
    parse_method: str = "raw"


@dataclass
class EmailMessage:
    message_id: str
    subject: str
    sender: str
    received_at: str
    body_text: str
    attachments: list[AttachmentPayload] = field(default_factory=list)
    raw_path: Path | None = None


@dataclass
class ProductLine:
    canonical_name: str
    requested_name: str
    quantity: str
    unit: str = ""
    notes: str = ""
    confidence: float = 0.0


@dataclass
class ExtractionResult:
    message_id: str
    is_product_request: bool
    confidence: float
    customer_name: str = ""
    customer_email: str = ""
    requested_lines: list[ProductLine] = field(default_factory=list)
    freeform_notes: str = ""
    failure_reason: str = ""
    raw_model_output: dict[str, Any] = field(default_factory=dict)
