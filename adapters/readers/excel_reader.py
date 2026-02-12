"""Excel (XLSX) reader implementation.

Reads agency-specific Excel files based on mapping definitions
and converts them to the CIR model.
"""

from __future__ import annotations

from pathlib import Path

import openpyxl

from adapters.mapping import MappingDefinition
from adapters.readers.base import BaseReader
from core.models import DMP


class ExcelReader(BaseReader):
    """Reads data from an Excel file based on a mapping definition."""

    def __init__(self, mapping: MappingDefinition) -> None:
        self._mapping = mapping

    def read(self, input_path: Path) -> DMP:
        """Read an Excel file and return the CIR representation."""
        wb = openpyxl.load_workbook(input_path, data_only=True)
        raw: dict[str, str | None] = {}

        for field_key, field_mapping in self._mapping.fields.items():
            if field_mapping.excel_cell is None:
                continue
            sheet_name = field_mapping.excel_sheet or wb.sheetnames[0]
            ws = wb[sheet_name]
            raw[field_mapping.cir_path] = ws[field_mapping.excel_cell].value

        wb.close()
        return self._build_dmp(raw)

    def _build_dmp(self, raw: dict[str, str | None]) -> DMP:
        """Build a DMP from raw cell values.

        This is a minimal scaffold. Full implementation will map
        flat cell values into the nested CIR structure.
        """
        raise NotImplementedError(
            "ExcelReader._build_dmp must be implemented for each agency format"
        )
