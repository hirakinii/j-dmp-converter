"""Mapping definition loader.

Loads YAML mapping files that define the correspondence between
agency-specific file coordinates and CIR field paths.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class FieldMapping:
    """Mapping of one CIR field to a file coordinate."""

    cir_path: str
    excel_cell: str | None = None
    excel_sheet: str | None = None
    word_table: int | None = None
    word_row: int | None = None
    word_col: int | None = None
    required: bool = False


@dataclass
class MappingDefinition:
    """Complete mapping definition for one agency format."""

    format_id: str
    format_name: str
    file_type: str  # "xlsx" or "docx"
    fields: dict[str, FieldMapping] = field(default_factory=dict)


def load_mapping(path: Path) -> MappingDefinition:
    """Load a mapping definition from a YAML file."""
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    meta = data.get("meta", {})
    definition = MappingDefinition(
        format_id=meta.get("format_id", path.stem),
        format_name=meta.get("format_name", path.stem),
        file_type=meta.get("file_type", "xlsx"),
    )

    for key, value in data.get("mapping", {}).items():
        definition.fields[key] = FieldMapping(
            cir_path=value.get("cir_path", ""),
            excel_cell=value.get("excel_cell"),
            excel_sheet=value.get("excel_sheet"),
            word_table=value.get("word_table"),
            word_row=value.get("word_row"),
            word_col=value.get("word_col"),
            required=value.get("required", False),
        )

    return definition
