from __future__ import annotations

from app.core.config import settings
from app.models.entities import ExtractionResult
from app.services.catalog import CatalogService
from app.services.email_ingest import InboxConnector
from app.services.excel import ExcelWriter
from app.services.llm import ExtractionEngine
from app.services.parser import AttachmentParser
from app.services.reporting import FailureReporter


class ProcessingPipeline:
    def __init__(self) -> None:
        self.catalog = CatalogService(settings.canonical_catalog_path)
        self.connector = InboxConnector()
        self.parser = AttachmentParser()
        self.extractor = ExtractionEngine(self.catalog)
        self.writer = ExcelWriter(settings.output_workbook_path, settings.template_workbook_path)
        self.reporter = FailureReporter(settings.data_dir / "failures")

    def run_once(self) -> list[ExtractionResult]:
        results: list[ExtractionResult] = []
        messages = self.connector.fetch_new_messages()
        for message in messages:
            enriched = self.parser.enrich(message)
            result = self.extractor.extract(enriched)
            self.writer.append_result(enriched, result)
            self.reporter.record(enriched, result)
            results.append(result)
        return results
