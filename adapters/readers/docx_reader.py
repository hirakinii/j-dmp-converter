"""DOCX (Word) reader implementation.

Reads agency-specific Word files based on mapping definitions,
focusing on Table structures for data extraction.
Uses word_table, word_row, word_col coordinates from the mapping.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from docx import Document

from adapters.mapping import MappingDefinition
from adapters.readers.base import BaseReader
from adapters.readers.excel_reader import _parse_datetime, _unflatten
from core.models import DMP


class DocxReader(BaseReader):
    """Reads data from a Word file based on table coordinates in the mapping."""

    def __init__(self, mapping: MappingDefinition) -> None:
        """Initialize the DocxReader.

        Args:
            mapping: Mapping definition linking table coordinates to CIR fields.
        """
        self._mapping = mapping

    def read(self, input_path: Path) -> DMP:
        """Read a Word file and return the CIR representation."""
        doc = Document(input_path.as_posix())
        tables = doc.tables
        raw: dict[str, str | None] = {}

        for field_key, field_mapping in self._mapping.fields.items():
            if field_mapping.word_table is None:
                continue
            table_idx = field_mapping.word_table
            row_idx = field_mapping.word_row
            col_idx = field_mapping.word_col
            if row_idx is None or col_idx is None:
                continue
            if table_idx >= len(tables):
                continue
            table = tables[table_idx]
            if row_idx >= len(table.rows):
                continue
            row = table.rows[row_idx]
            if col_idx >= len(row.cells):
                continue
            cell_text = row.cells[col_idx].text.strip()
            if cell_text:
                raw[field_mapping.cir_path] = cell_text

        return self._build_dmp(raw)

    def _build_dmp(self, raw: dict[str, str | None]) -> DMP:
        """Build a DMP from raw cell values.

        Converts flat dot-path keyed values into the nested structure
        expected by the DMP Pydantic model, providing defaults for
        required fields not present in the source file.
        """
        nested = _unflatten(raw)
        now = datetime.now(timezone.utc)

        # Ensure required top-level fields have defaults
        nested.setdefault("title", nested.get("project", [{}])[0].get("title", "Untitled DMP"))
        nested.setdefault(
            "dmp_id",
            {"identifier": f"import-{self._mapping.format_id}", "type": "other"},
        )
        nested.setdefault("language", "jpn")
        nested.setdefault("ethical_issues_exist", "unknown")

        # Handle created/modified
        if "created" in nested:
            if isinstance(nested["created"], str):
                nested["created"] = _parse_datetime(nested["created"]) or now
        else:
            nested["created"] = now
        if "modified" in nested:
            if isinstance(nested["modified"], str):
                nested["modified"] = _parse_datetime(nested["modified"]) or now
        else:
            nested["modified"] = now

        # Ensure contact exists with required fields
        if "contact" not in nested:
            nested["contact"] = {}
        contact = nested["contact"]
        contact.setdefault("name", "Unknown")
        contact.setdefault("mbox", "unknown@example.com")
        contact.setdefault("contact_id", {"identifier": "unknown", "type": "other"})

        # Ensure projects have required fields
        for proj in nested.get("project", []):
            proj.setdefault("title", "Untitled Project")

        # Ensure contributors have required fields
        for contrib in nested.get("contributor", []):
            contrib.setdefault("contributor_id", {"identifier": "unknown", "type": "other"})
            contrib.setdefault("name", "Unknown")

        # Ensure at least one dataset exists
        if "dataset" not in nested:
            nested["dataset"] = [{}]
        for ds in nested["dataset"]:
            ds.setdefault("title", "Untitled Dataset")
            ds.setdefault("dataset_id", {"identifier": "unknown", "type": "other"})
            ds.setdefault("personal_data", "unknown")
            ds.setdefault("sensitive_data", "unknown")
            for dist in ds.get("distribution", []):
                dist.setdefault("title", ds.get("title", "Untitled"))
                dist.setdefault("data_access", "closed")
                if "host" in dist:
                    dist["host"].setdefault("title", "Unknown Repository")
                    dist["host"].setdefault("url", "")
            for sp in ds.get("security_and_privacy", []):
                sp.setdefault("title", "Security and Privacy")

        return DMP.model_validate(nested)
