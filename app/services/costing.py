from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CostEstimate:
    monthly_emails: int
    estimated_monthly_cost_low: float
    estimated_monthly_cost_high: float
    assumptions: list[str]


def estimate_monthly_cost(emails_per_day: int = 20) -> CostEstimate:
    monthly_emails = emails_per_day * 30
    low = round(monthly_emails * 0.015, 2)
    high = round(monthly_emails * 0.075, 2)
    assumptions = [
        "One extraction pass per email.",
        "OCR runs locally when possible.",
        "ZIP files increase parse volume and may push cost toward the upper bound.",
        "A validator pass is reserved for low-confidence cases only.",
    ]
    return CostEstimate(monthly_emails, low, high, assumptions)
