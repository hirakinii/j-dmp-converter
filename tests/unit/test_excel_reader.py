"""Tests for the Excel reader (Step 2.1 of implementation plan).

These tests verify that data can be read from Excel files
and converted back to CIR (DMP) models.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict
import openpyxl
import pytest

from adapters.mapping import load_mapping
from adapters.readers.excel_reader import ExcelReader, _unflatten
from adapters.writers.excel_writer import ExcelWriter
from core.models import DMP

DEFINITIONS_DIR = Path(__file__).resolve().parent.parent.parent / "adapters" / "definitions"
TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "adapters" / "templates"


class TestUnflatten:
    """Test the unflatten helper function."""

    def test_simple_key(self) -> None:
        result = _unflatten({"title": "hello"})
        assert result == {"title": "hello"}

    def test_nested_key(self) -> None:
        result = _unflatten({"contact.name": "山田太郎"})
        assert result == {"contact": {"name": "山田太郎"}}

    def test_list_index(self) -> None:
        result = _unflatten({"project.0.title": "研究"})
        assert result == {"project": [{"title": "研究"}]}

    def test_deep_nested(self) -> None:
        result = _unflatten({
            "dataset.0.distribution.0.host.url": "https://example.com"
        })
        assert result["dataset"][0]["distribution"][0]["host"]["url"] == "https://example.com"

    def test_multiple_fields(self) -> None:
        result = _unflatten({
            "contact.name": "山田太郎",
            "contact.affiliation.0.name": "東京大学",
            "project.0.title": "研究プロジェクト",
        })
        assert result["contact"]["name"] == "山田太郎"
        assert result["contact"]["affiliation"][0]["name"] == "東京大学"
        assert result["project"][0]["title"] == "研究プロジェクト"

    def test_none_values_skipped(self) -> None:
        result = _unflatten({"title": "hello", "description": None})
        assert "description" not in result


class TestExcelReaderBuildDmp:
    """Test that ExcelReader builds valid DMP models from raw data."""

    def test_build_dmp_with_minimal_data(self) -> None:
        """Reader should build a valid DMP with sensible defaults."""
        mapping = load_mapping(DEFINITIONS_DIR / "amed_dmp.yaml")
        reader = ExcelReader(mapping=mapping)
        raw: Dict[str, str | None] = {
            "project.0.title": "テストプロジェクト",
            "contact.name": "田中花子",
            "dataset.0.title": "テストデータ",
        }
        dmp = reader._build_dmp(raw)
        assert dmp.title == "テストプロジェクト"
        assert dmp.contact.name == "田中花子"
        assert dmp.dataset[0].title == "テストデータ"

    def test_build_dmp_defaults_for_missing_fields(self) -> None:
        """Reader should provide defaults for required fields not in Excel."""
        mapping = load_mapping(DEFINITIONS_DIR / "amed_dmp.yaml")
        reader = ExcelReader(mapping=mapping)
        raw: Dict[str, str | None] = {"project.0.title": "研究A"}
        dmp = reader._build_dmp(raw)
        assert dmp.dmp_id.type == "other"
        assert dmp.language == "jpn"
        assert dmp.contact.name == "Unknown"
        assert len(dmp.dataset) >= 1


class TestExcelReaderRoundTrip:
    """Test write -> read round-trip for each format."""

    def test_amed_round_trip(self, sample_dmp: DMP, tmp_path: Path) -> None:
        """Writing AMED then reading should recover key fields."""
        mapping = load_mapping(DEFINITIONS_DIR / "amed_dmp.yaml")
        writer = ExcelWriter(mapping=mapping, template_path=TEMPLATES_DIR / "amed_template.xlsx")
        reader = ExcelReader(mapping=mapping)

        output = tmp_path / "amed_output.xlsx"
        writer.write(sample_dmp, output)
        recovered = reader.read(output)

        assert recovered.contact.name == "山田太郎"
        assert recovered.project[0].title == "サンプル研究プロジェクト"
        assert recovered.dataset[0].title == "実験データセット"

    def test_jsps_round_trip(self, sample_dmp: DMP, tmp_path: Path) -> None:
        """Writing JSPS then reading should recover key fields."""
        mapping = load_mapping(DEFINITIONS_DIR / "jsps_dmp.yaml")
        writer = ExcelWriter(mapping=mapping, template_path=TEMPLATES_DIR / "jsps_template.xlsx")
        reader = ExcelReader(mapping=mapping)

        output = tmp_path / "jsps_output.xlsx"
        writer.write(sample_dmp, output)
        recovered = reader.read(output)

        assert recovered.contact.name == "山田太郎"
        assert recovered.dataset[0].title == "実験データセット"

    def test_meti_round_trip(self, sample_dmp: DMP, tmp_path: Path) -> None:
        """Writing METI then reading should recover key fields."""
        mapping = load_mapping(DEFINITIONS_DIR / "meti_dmp.yaml")
        writer = ExcelWriter(mapping=mapping, template_path=TEMPLATES_DIR / "meti_template.xlsx")
        reader = ExcelReader(mapping=mapping)

        output = tmp_path / "meti_output.xlsx"
        writer.write(sample_dmp, output)
        recovered = reader.read(output)

        assert recovered.project[0].title == "サンプル研究プロジェクト"
        assert recovered.dataset[0].title == "実験データセット"
