from __future__ import annotations

from app.models.entities import ExtractionResult


class QualityGate:
    def __init__(self, confidence_threshold: float = 0.86) -> None:
        self.confidence_threshold = confidence_threshold

    def should_review(self, result: ExtractionResult) -> bool:
        if not result.is_product_request:
            return False
        if result.failure_reason or not result.requested_lines:
            return True
        return any((not line.canonical_name) or line.confidence < self.confidence_threshold for line in result.requested_lines)
