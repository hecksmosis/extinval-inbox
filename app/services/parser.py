from __future__ import annotations

import importlib
import zipfile
from pathlib import Path

from app.core.config import settings
from app.models.entities import AttachmentPayload, EmailMessage


class AttachmentParser:
    def __init__(self) -> None:
        self._parser = self._build_llama_parser()

    def _build_llama_parser(self):
        if not settings.llama_parse_api_key:
            return None
        module_spec = importlib.util.find_spec("llama_parse")
        if module_spec is None:
            return None
        module = importlib.import_module("llama_parse")
        parser_cls = getattr(module, "LlamaParse")
        return parser_cls(api_key=settings.llama_parse_api_key, result_type="markdown")

    def enrich(self, message: EmailMessage) -> EmailMessage:
        enriched: list[AttachmentPayload] = []
        for attachment in message.attachments:
            if attachment.filename.lower().endswith(".zip"):
                enriched.extend(self._extract_zip(attachment))
            else:
                attachment.extracted_text, attachment.parse_method = self._parse_path(attachment.path)
                enriched.append(attachment)
        message.attachments = enriched
        return message

    def _extract_zip(self, attachment: AttachmentPayload) -> list[AttachmentPayload]:
        results: list[AttachmentPayload] = []
        with zipfile.ZipFile(attachment.path) as archive:
            for index, member in enumerate(archive.infolist()[: settings.max_zip_members]):
                if member.is_dir():
                    continue
                target = settings.audit_dir / f"zip_{index}_{Path(member.filename).name}"
                target.write_bytes(archive.read(member.filename))
                text, method = self._parse_path(target)
                results.append(
                    AttachmentPayload(
                        filename=Path(member.filename).name,
                        content_type="application/octet-stream",
                        path=target,
                        extracted_text=text,
                        parse_method=method,
                    )
                )
        return results

    def _parse_path(self, path: Path) -> tuple[str, str]:
        suffix = path.suffix.lower()
        if suffix in {".txt", ".csv", ".json"}:
            return path.read_text(errors="ignore"), "native"
        if self._parser is not None:
            docs = self._parser.load_data(str(path))
            return "\n\n".join(getattr(doc, "text", str(doc)) for doc in docs), "llamaparse"
        if suffix in {".png", ".jpg", ".jpeg", ".pdf", ".tif", ".tiff"}:
            return "OCR required but local OCR not configured.", "ocr-fallback"
        return f"Binary attachment saved at {path.name}", "raw-binary"
