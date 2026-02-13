"""Tests for the Excel reader (Step 2.1 of implementation plan).

These tests verify that data can be read from Excel files
and converted back to CIR (DMP) models.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

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


FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


class TestAmedReader:
    """Test reading a pre-filled AMED Excel file (Step 2.1).

    Uses a fixture file (filled_amed_sample.xlsx) that simulates
    a real AMED DMP form filled out by a researcher.
    """

    @pytest.fixture
    def amed_dmp(self) -> DMP:
        """Read the pre-filled AMED fixture and return the CIR."""
        mapping = load_mapping(DEFINITIONS_DIR / "amed_dmp.yaml")
        reader = ExcelReader(mapping=mapping)
        return reader.read(FIXTURES_DIR / "filled_amed_sample.xlsx")

    def test_project_title(self, amed_dmp: DMP) -> None:
        """Reader should extract the project title from the AMED form."""
        assert amed_dmp.project[0].title == "データマネジメント支援ツールの開発"

    def test_contact_name(self, amed_dmp: DMP) -> None:
        """Reader should extract the PI name from the AMED form."""
        assert amed_dmp.contact.name == "鈴木一郎"

    def test_contact_affiliation(self, amed_dmp: DMP) -> None:
        """Reader should extract the PI affiliation from the AMED form."""
        assert amed_dmp.contact.affiliation[0].name == "京都大学"

    def test_dataset_title(self, amed_dmp: DMP) -> None:
        """Reader should extract the dataset title from the AMED form."""
        assert amed_dmp.dataset[0].title == "臨床試験データ"

    def test_dataset_description(self, amed_dmp: DMP) -> None:
        """Reader should extract the dataset description from the AMED form."""
        assert amed_dmp.dataset[0].description == "臨床試験から得られたデータセット"

    def test_data_access(self, amed_dmp: DMP) -> None:
        """Reader should extract data access policy from the AMED form."""
        assert amed_dmp.dataset[0].distribution[0].data_access == "open"

    def test_repository_url(self, amed_dmp: DMP) -> None:
        """Reader should extract repository URL from the AMED form."""
        assert amed_dmp.dataset[0].distribution[0].host.url == "https://repository.kyoto-u.ac.jp"

    def test_contributor_name(self, amed_dmp: DMP) -> None:
        """Reader should extract the data manager name from the AMED form."""
        assert amed_dmp.contributor[0].name == "佐藤花子"

    def test_contributor_mbox(self, amed_dmp: DMP) -> None:
        """Reader should extract the data manager email from the AMED form."""
        assert amed_dmp.contributor[0].mbox == "sato@example.kyoto-u.ac.jp"

    def test_erad_project_id(self, amed_dmp: DMP) -> None:
        """Reader should extract the e-Rad project ID from the AMED form."""
        assert amed_dmp.project[0].erad_project_id == "JP26000099"


class TestJspsReader:
    """Test reading a pre-filled JSPS Excel file.

    Uses a fixture file (filled_jsps_sample.xlsx) that simulates
    a real JSPS DMP form filled out by a researcher.
    """

    @pytest.fixture
    def jsps_dmp(self) -> DMP:
        """Read the pre-filled JSPS fixture and return the CIR."""
        mapping = load_mapping(DEFINITIONS_DIR / "jsps_dmp.yaml")
        reader = ExcelReader(mapping=mapping)
        return reader.read(FIXTURES_DIR / "filled_jsps_sample.xlsx")

    def test_project_erad_id(self, jsps_dmp: DMP) -> None:
        """Reader should extract the e-Rad project ID from the JSPS form."""
        assert jsps_dmp.project[0].erad_project_id == "JP26000055"

    def test_contact_name(self, jsps_dmp: DMP) -> None:
        """Reader should extract the PI name from the JSPS form."""
        assert jsps_dmp.contact.name == "高橋誠"

    def test_contact_affiliation(self, jsps_dmp: DMP) -> None:
        """Reader should extract the PI affiliation from the JSPS form."""
        assert jsps_dmp.contact.affiliation[0].name == "大阪大学"

    def test_contact_mbox(self, jsps_dmp: DMP) -> None:
        """Reader should extract the PI email from the JSPS form."""
        assert jsps_dmp.contact.mbox == "takahashi@example.osaka-u.ac.jp"

    def test_dataset_title(self, jsps_dmp: DMP) -> None:
        """Reader should extract the dataset title from the JSPS form."""
        assert jsps_dmp.dataset[0].title == "気象観測データ"

    def test_dataset_description(self, jsps_dmp: DMP) -> None:
        """Reader should extract the dataset description from the JSPS form."""
        assert jsps_dmp.dataset[0].description == "全国の気象観測所から収集したデータ"

    def test_data_access(self, jsps_dmp: DMP) -> None:
        """Reader should extract data access policy from the JSPS form."""
        assert jsps_dmp.dataset[0].distribution[0].data_access == "open"

    def test_repository_url(self, jsps_dmp: DMP) -> None:
        """Reader should extract repository URL from the JSPS form."""
        assert jsps_dmp.dataset[0].distribution[0].host.url == "https://repository.osaka-u.ac.jp"

    def test_security_and_privacy(self, jsps_dmp: DMP) -> None:
        """Reader should extract security/privacy info from the JSPS form."""
        assert jsps_dmp.dataset[0].security_and_privacy[0].description == "個人情報を含まない"


class TestMetiReader:
    """Test reading a pre-filled METI Excel file.

    Uses a fixture file (filled_meti_sample.xlsx) that simulates
    a real METI DMP form filled out by a researcher.
    """

    @pytest.fixture
    def meti_dmp(self) -> DMP:
        """Read the pre-filled METI fixture and return the CIR."""
        mapping = load_mapping(DEFINITIONS_DIR / "meti_dmp.yaml")
        reader = ExcelReader(mapping=mapping)
        return reader.read(FIXTURES_DIR / "filled_meti_sample.xlsx")

    def test_project_title(self, meti_dmp: DMP) -> None:
        """Reader should extract the project title from the METI form."""
        assert meti_dmp.project[0].title == "次世代エネルギー材料の開発"

    def test_dataset_title(self, meti_dmp: DMP) -> None:
        """Reader should extract the dataset title from the METI form."""
        assert meti_dmp.dataset[0].title == "エネルギー材料特性データ"

    def test_dataset_description(self, meti_dmp: DMP) -> None:
        """Reader should extract the dataset description from the METI form."""
        assert meti_dmp.dataset[0].description == "新規材料の物性測定データ"

    def test_data_management_institution(self, meti_dmp: DMP) -> None:
        """Reader should extract the management institution from the METI form."""
        assert meti_dmp.contributor[0].affiliation[0].name == "東北大学材料科学研究所"

    def test_data_access(self, meti_dmp: DMP) -> None:
        """Reader should extract data access policy from the METI form."""
        assert meti_dmp.dataset[0].distribution[0].data_access == "shared"
