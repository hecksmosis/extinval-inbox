from __future__ import annotations

import importlib
from pathlib import Path

from app.models.entities import EmailMessage, ExtractionResult


class ExcelWriter:
    headers = [
        "message_id",
        "received_at",
        "sender",
        "subject",
        "customer_name",
        "customer_email",
        "canonical_name",
        "requested_name",
        "quantity",
        "unit",
        "line_notes",
        "line_confidence",
        "email_notes",
    ]

    def __init__(self, output_path: Path, template_path: Path | None = None):
        self.output_path = output_path
        self.template_path = template_path if template_path and template_path.exists() else None

    def append_result(self, message: EmailMessage, result: ExtractionResult) -> None:
        load_workbook, workbook_factory = self._workbook_api()
        workbook = self._open_or_create(load_workbook, workbook_factory)
        sheet = workbook.active
        if sheet.max_row == 1 and sheet["A1"].value is None:
            sheet.append(self.headers)
        if result.requested_lines:
            for line in result.requested_lines:
                sheet.append([
                    result.message_id,
                    message.received_at,
                    message.sender,
                    message.subject,
                    result.customer_name,
                    result.customer_email,
                    line.canonical_name,
                    line.requested_name,
                    line.quantity,
                    line.unit,
                    line.notes,
                    line.confidence,
                    result.freeform_notes,
                ])
        else:
            sheet.append([
                result.message_id,
                message.received_at,
                message.sender,
                message.subject,
                result.customer_name,
                result.customer_email,
                "",
                "",
                "",
                "",
                result.failure_reason,
                result.confidence,
                result.freeform_notes,
            ])
        workbook.save(self.output_path)

    def _workbook_api(self):
        if importlib.util.find_spec('openpyxl') is None:
            raise RuntimeError('openpyxl is required to write Excel workbooks.')
        module = importlib.import_module('openpyxl')
        return getattr(module, 'load_workbook'), getattr(module, 'Workbook')

    def _open_or_create(self, load_workbook, workbook_factory):
        if self.output_path.exists():
            return load_workbook(self.output_path)
        if self.template_path:
            return load_workbook(self.template_path)
        return workbook_factory()
