"""Tests for the Excel writer (Step 1.2 of implementation plan).

These tests verify that CIR data is correctly injected into
Excel templates based on mapping definitions.
"""

from __future__ import annotations

from pathlib import Path

import openpyxl
import pytest

from adapters.mapping import load_mapping
from adapters.writers.excel_writer import ExcelWriter
from core.models import DMP

DEFINITIONS_DIR = Path(__file__).resolve().parent.parent.parent / "adapters" / "definitions"
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture
def amed_template(tmp_path: Path) -> Path:
    """Create a minimal AMED template Excel file for testing."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "DMP"
    # Set up header-like structure (simplified)
    ws["A5"] = "研究代表者"
    ws["A7"] = "研究課題名"
    ws["A12"] = "データセット名"
    wb.save(tmp_path / "amed_template.xlsx")
    wb.close()
    return tmp_path / "amed_template.xlsx"


class TestExcelWriter:
    def test_write_contact_name(
        self, sample_dmp: DMP, amed_template: Path, tmp_path: Path
    ) -> None:
        """Writer should inject contact name into the correct cell."""
        mapping = load_mapping(DEFINITIONS_DIR / "amed_dmp.yaml")
        writer = ExcelWriter(mapping=mapping, template_path=amed_template)

        output = tmp_path / "output.xlsx"
        writer.write(sample_dmp, output)

        wb = openpyxl.load_workbook(output)
        ws = wb[wb.sheetnames[0]]
        assert ws["B5"].value == "山田太郎"
        wb.close()

    def test_write_project_title(
        self, sample_dmp: DMP, amed_template: Path, tmp_path: Path
    ) -> None:
        """Writer should inject project title into the correct cell."""
        mapping = load_mapping(DEFINITIONS_DIR / "amed_dmp.yaml")
        writer = ExcelWriter(mapping=mapping, template_path=amed_template)

        output = tmp_path / "output.xlsx"
        writer.write(sample_dmp, output)

        wb = openpyxl.load_workbook(output)
        ws = wb[wb.sheetnames[0]]
        assert ws["B7"].value == "サンプル研究プロジェクト"
        wb.close()

    def test_write_dataset_title(
        self, sample_dmp: DMP, amed_template: Path, tmp_path: Path
    ) -> None:
        """Writer should inject dataset title into the correct cell."""
        mapping = load_mapping(DEFINITIONS_DIR / "amed_dmp.yaml")
        writer = ExcelWriter(mapping=mapping, template_path=amed_template)

        output = tmp_path / "output.xlsx"
        writer.write(sample_dmp, output)

        wb = openpyxl.load_workbook(output)
        ws = wb[wb.sheetnames[0]]
        assert ws["B12"].value == "実験データセット"
        wb.close()


class TestExcelWriterValidation:
    def test_validate_complete_dmp_for_amed(self, sample_dmp: DMP, amed_template: Path) -> None:
        """A complete DMP should pass AMED validation."""
        mapping = load_mapping(DEFINITIONS_DIR / "amed_dmp.yaml")
        writer = ExcelWriter(mapping=mapping, template_path=amed_template)
        result = writer.validate(sample_dmp)
        assert result.is_complete

    def test_validate_detects_missing_jsps_fields(
        self, sample_dmp: DMP, amed_template: Path
    ) -> None:
        """JSPS requires more fields — validation should detect gaps."""
        mapping = load_mapping(DEFINITIONS_DIR / "jsps_dmp.yaml")
        writer = ExcelWriter(mapping=mapping, template_path=amed_template)
        result = writer.validate(sample_dmp)
        # JSPS requires preservation_statement which our sample doesn't have
        missing_paths = [f.field_path for f in result.missing_fields]
        assert "dataset.0.preservation_statement" in missing_paths
