from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import json

from app.models.entities import EmailMessage, ExtractionResult


class FailureReporter:
    def __init__(self, report_dir: Path):
        self.report_dir = report_dir
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def record(self, message: EmailMessage, result: ExtractionResult) -> None:
        if self.is_failure(result):
            payload = {
                "email": {
                    "message_id": message.message_id,
                    "subject": message.subject,
                    "sender": message.sender,
                    "received_at": message.received_at,
                },
                "extraction": asdict(result),
            }
            target = self.report_dir / f"failure_{self._safe_name(message.message_id)}.json"
            target.write_text(json.dumps(payload, indent=2))

    @staticmethod
    def is_failure(result: ExtractionResult) -> bool:
        if not result.is_product_request:
            return False
        if result.failure_reason:
            return True
        if not result.requested_lines:
            return True
        return any((not line.canonical_name) or line.confidence < 0.86 for line in result.requested_lines)

    @staticmethod
    def _safe_name(text: str) -> str:
        return "".join(char if char.isalnum() else "_" for char in text)[:80]
