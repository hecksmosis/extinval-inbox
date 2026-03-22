from __future__ import annotations

import importlib
import json
from dataclasses import asdict

from app.core.config import settings
from app.models.entities import EmailMessage, ExtractionResult, ProductLine
from app.services.catalog import CatalogService


class ExtractionEngine:
    def __init__(self, catalog: CatalogService):
        self.catalog = catalog

    def extract(self, message: EmailMessage) -> ExtractionResult:
        prompt = self._build_prompt(message)
        if not settings.model_api_key:
            return self._fallback_extract(message)
        return self._extract_with_retry(message, prompt)

    def _extract_with_retry(self, message: EmailMessage, prompt: str) -> ExtractionResult:
        for _ in range(3):
            try:
                if settings.model_provider == "gemini":
                    payload = self._call_gemini(prompt)
                else:
                    payload = self._call_claude(prompt)
                return self._normalize_payload(message, payload)
            except Exception:
                continue
        fallback = self._fallback_extract(message)
        fallback.failure_reason = 'Model extraction failed after retries.'
        return fallback

    def _build_prompt(self, message: EmailMessage) -> str:
        attachment_text = "\n\n".join(
            f"Attachment: {a.filename}\nMethod: {a.parse_method}\nContent:\n{a.extracted_text}" for a in message.attachments
        )
        return f"""
You classify whether this email is a product request for Extinval.
Return JSON only with fields:
message_id, is_product_request, confidence, customer_name, customer_email, freeform_notes,
requested_lines[{requested_name, canonical_name, quantity, unit, notes, confidence}], failure_reason.
Rules:
- Never invent products.
- canonical_name must be selected from this catalog only:
{self.catalog.to_prompt_block()}
- If uncertain, leave canonical_name blank and explain in notes.
- Product requests may appear in arbitrary prose, images, scanned PDFs, or zip-contained PDFs.
- Aggregate all product lines from the entire email context.

Email subject: {message.subject}
From: {message.sender}
Date: {message.received_at}
Body:
{message.body_text}

Attachments:
{attachment_text}
""".strip()

    def _httpx(self):
        if importlib.util.find_spec('httpx') is None:
            raise RuntimeError('httpx is required for hosted model calls.')
        return importlib.import_module('httpx')

    def _call_gemini(self, prompt: str) -> dict:
        httpx = self._httpx()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.model_name}:generateContent?key={settings.model_api_key}"
        body = {
            "generationConfig": {"temperature": settings.model_temperature, "response_mime_type": "application/json"},
            "contents": [{"parts": [{"text": prompt}]}],
        }
        response = httpx.post(url, json=body, timeout=120)
        response.raise_for_status()
        text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)

    def _call_claude(self, prompt: str) -> dict:
        httpx = self._httpx()
        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.model_api_key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": settings.model_name,
                "max_tokens": 3000,
                "temperature": settings.model_temperature,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=120,
        )
        response.raise_for_status()
        text = response.json()["content"][0]["text"]
        return json.loads(text)

    def _normalize_payload(self, message: EmailMessage, payload: dict) -> ExtractionResult:
        lines = [
            ProductLine(
                canonical_name=item.get("canonical_name", ""),
                requested_name=item.get("requested_name", ""),
                quantity=str(item.get("quantity", "")),
                unit=item.get("unit", ""),
                notes=item.get("notes", ""),
                confidence=float(item.get("confidence", 0.0)),
            )
            for item in payload.get("requested_lines", [])
        ]
        return ExtractionResult(
            message_id=payload.get("message_id", message.message_id),
            is_product_request=bool(payload.get("is_product_request", False)),
            confidence=float(payload.get("confidence", 0.0)),
            customer_name=payload.get("customer_name", ""),
            customer_email=payload.get("customer_email", ""),
            requested_lines=lines,
            freeform_notes=payload.get("freeform_notes", ""),
            failure_reason=payload.get("failure_reason", ""),
            raw_model_output=payload,
        )

    def _fallback_extract(self, message: EmailMessage) -> ExtractionResult:
        body = f"{message.subject}\n{message.body_text}".lower()
        is_request = any(keyword in body for keyword in ["quote", "request", "need", "extinguisher", "product"])
        return ExtractionResult(
            message_id=message.message_id,
            is_product_request=is_request,
            confidence=0.4 if is_request else 0.2,
            freeform_notes="Fallback heuristic used because no model API key is configured.",
            raw_model_output={"mode": "fallback"},
        )

    @staticmethod
    def to_json(result: ExtractionResult) -> str:
        return json.dumps(asdict(result), indent=2)
