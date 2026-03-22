from __future__ import annotations

import csv
from pathlib import Path


class CatalogService:
    def __init__(self, catalog_path: Path):
        self.catalog_path = catalog_path
        self._catalog = self._load_catalog()

    def _load_catalog(self) -> list[dict[str, str]]:
        suffix = self.catalog_path.suffix.lower()
        if suffix in {'.xlsx', '.xls'}:
            raise ValueError('Excel catalog loading requires conversion to CSV in this scaffolded build.')
        with self.catalog_path.open(newline='', encoding='utf-8') as handle:
            reader = csv.DictReader(handle)
            rows = []
            for row in reader:
                normalized = {str(key).strip().lower(): str(value or '').strip() for key, value in row.items()}
                rows.append(normalized)
        if not rows:
            return []
        if 'canonical_name' not in rows[0]:
            raise ValueError("Catalog must include a 'canonical_name' column")
        for row in rows:
            row.setdefault('aliases', '')
        return rows

    @property
    def canonical_names(self) -> list[str]:
        return [row['canonical_name'] for row in self._catalog]

    def to_prompt_block(self) -> str:
        lines: list[str] = []
        for row in self._catalog:
            alias_text = f" | aliases: {row['aliases']}" if row.get('aliases') else ''
            lines.append(f"- {row['canonical_name']}{alias_text}")
        return '\n'.join(lines)
