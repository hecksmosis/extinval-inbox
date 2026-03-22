from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    app_name: str = os.getenv('APP_NAME', 'Extinval Inbox Automation')
    data_dir: Path = Path(os.getenv('DATA_DIR', 'runtime'))
    email_provider: str = os.getenv('EMAIL_PROVIDER', 'imap')
    email_host: str = os.getenv('EMAIL_HOST', '')
    email_port: int = int(os.getenv('EMAIL_PORT', '993'))
    email_username: str = os.getenv('EMAIL_USERNAME', '')
    email_password: str = os.getenv('EMAIL_PASSWORD', '')
    model_provider: str = os.getenv('MODEL_PROVIDER', 'gemini')
    model_name: str = os.getenv('MODEL_NAME', 'gemini-2.0-flash')
    model_api_key: str = os.getenv('MODEL_API_KEY', '')
    model_temperature: float = float(os.getenv('MODEL_TEMPERATURE', '0.0'))
    canonical_catalog_path: Path = Path(os.getenv('CANONICAL_CATALOG_PATH', 'assets/canonical_catalog.csv'))
    template_workbook_path: Path = Path(os.getenv('TEMPLATE_WORKBOOK_PATH', 'assets/template.xlsx'))
    output_workbook_path: Path = Path(os.getenv('OUTPUT_WORKBOOK_PATH', 'runtime/extinval_output.xlsx'))
    report_workbook_path: Path = Path(os.getenv('REPORT_WORKBOOK_PATH', 'runtime/extinval_failures.xlsx'))
    checkpoint_path: Path = Path(os.getenv('CHECKPOINT_PATH', 'runtime/checkpoint.json'))
    audit_dir: Path = Path(os.getenv('AUDIT_DIR', 'runtime/audit'))
    llama_parse_api_key: str = os.getenv('LLAMA_PARSE_API_KEY', '')
    confidence_threshold: float = float(os.getenv('CONFIDENCE_THRESHOLD', '0.86'))
    poll_interval_seconds: int = int(os.getenv('POLL_INTERVAL_SECONDS', '300'))
    local_ocr_enabled: bool = os.getenv('LOCAL_OCR_ENABLED', 'true').lower() == 'true'
    max_zip_members: int = int(os.getenv('MAX_ZIP_MEMBERS', '100'))

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.audit_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
