"""Startup registration for all readers and writers.

Loads mapping definitions and templates for all supported agency formats,
then registers them on the ConversionService instance.
"""

from __future__ import annotations

from pathlib import Path

from adapters.mapping import load_mapping
from adapters.readers.cir_json_reader import CirJsonReader
from adapters.readers.docx_reader import DocxReader
from adapters.readers.excel_reader import ExcelReader
from adapters.writers.cir_json_writer import CirJsonWriter
from adapters.writers.docx_writer import DocxWriter
from adapters.writers.excel_writer import ExcelWriter
from core.converter import ConversionService

DEFINITIONS_DIR = Path(__file__).resolve().parent.parent / "adapters" / "definitions"
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "adapters" / "templates"

# (format_id, definition_yaml, template_file)
FORMAT_REGISTRY: list[tuple[str, str, str]] = [
    ("amed", "amed_dmp.yaml", "amed_template.xlsx"),
    ("jsps", "jsps_dmp.yaml", "jsps_template.xlsx"),
    ("meti", "meti_dmp.yaml", "meti_template.xlsx"),
    ("cfa", "cfa_dmp.yaml", "cfa_template.docx"),
]


def register_all(converter: ConversionService) -> None:
    """Register all supported readers and writers on the converter."""
    for format_id, definition_file, template_file in FORMAT_REGISTRY:
        mapping = load_mapping(DEFINITIONS_DIR / definition_file)
        template_path = TEMPLATES_DIR / template_file

        if mapping.file_type == "xlsx":
            converter.register_reader(format_id, ExcelReader(mapping=mapping))
            converter.register_writer(
                format_id,
                ExcelWriter(mapping=mapping, template_path=template_path),
            )
        elif mapping.file_type == "docx":
            converter.register_reader(format_id, DocxReader(mapping=mapping))
            converter.register_writer(
                format_id,
                DocxWriter(mapping=mapping, template_path=template_path),
            )

    # CIR JSON format (no mapping/template needed)
    converter.register_reader("cir", CirJsonReader())
    converter.register_writer("cir", CirJsonWriter())
