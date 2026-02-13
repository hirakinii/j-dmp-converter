"""Tests for the DOCX reader (Step 3.2 of implementation plan).

These tests verify that data can be read from Word files
(focusing on Table structures) and converted to CIR (DMP) models.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from adapters.mapping import load_mapping
from adapters.readers.docx_reader import DocxReader
from adapters.writers.docx_writer import DocxWriter
from core.models import DMP

DEFINITIONS_DIR = Path(__file__).resolve().parent.parent.parent / "adapters" / "definitions"
TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "adapters" / "templates"
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


class TestCfaReader:
    """Test reading a pre-filled CFA Word file (Step 3.2).

    Uses a fixture file (filled_cfa_sample.docx) that simulates
    a real CFA DMP form filled out by a researcher.
    """

    @pytest.fixture
    def cfa_dmp(self) -> DMP:
        """Read the pre-filled CFA fixture and return the CIR."""
        mapping = load_mapping(DEFINITIONS_DIR / "cfa_dmp.yaml")
        reader = DocxReader(mapping=mapping)
        return reader.read(FIXTURES_DIR / "filled_cfa_sample.docx")

    def test_project_title(self, cfa_dmp: DMP) -> None:
        """Reader should extract the project title from the CFA form."""
        assert cfa_dmp.project[0].title == "量子コンピューティング基盤技術の研究"

    def test_contact_name(self, cfa_dmp: DMP) -> None:
        """Reader should extract the PI name from the CFA form."""
        assert cfa_dmp.contact.name == "中村太一"

    def test_contact_affiliation(self, cfa_dmp: DMP) -> None:
        """Reader should extract the PI affiliation from the CFA form."""
        assert cfa_dmp.contact.affiliation[0].name == "名古屋大学"

    def test_dataset_title(self, cfa_dmp: DMP) -> None:
        """Reader should extract the dataset title from the CFA form."""
        assert cfa_dmp.dataset[0].title == "量子ビット特性データ"

    def test_dataset_description(self, cfa_dmp: DMP) -> None:
        """Reader should extract the dataset description from the CFA form."""
        assert cfa_dmp.dataset[0].description == "超伝導量子ビットの特性測定データ"

    def test_data_access(self, cfa_dmp: DMP) -> None:
        """Reader should extract data access policy from the CFA form."""
        assert cfa_dmp.dataset[0].distribution[0].data_access == "open"

    def test_repository_url(self, cfa_dmp: DMP) -> None:
        """Reader should extract repository URL from the CFA form."""
        assert cfa_dmp.dataset[0].distribution[0].host.url == "https://repository.nagoya-u.ac.jp"

    def test_contributor_name(self, cfa_dmp: DMP) -> None:
        """Reader should extract the data manager name from the CFA form."""
        assert cfa_dmp.contributor[0].name == "田中美咲"

    def test_contributor_mbox(self, cfa_dmp: DMP) -> None:
        """Reader should extract the data manager email from the CFA form."""
        assert cfa_dmp.contributor[0].mbox == "tanaka@example.nagoya-u.ac.jp"

    def test_erad_project_id(self, cfa_dmp: DMP) -> None:
        """Reader should extract the project ID from the CFA form."""
        assert cfa_dmp.project[0].erad_project_id == "JP26000077"


class TestDocxReaderRoundTrip:
    """Test write -> read round-trip for CFA DOCX format."""

    def test_cfa_round_trip(self, sample_dmp: DMP, tmp_path: Path) -> None:
        """Writing CFA then reading should recover key fields."""
        mapping = load_mapping(DEFINITIONS_DIR / "cfa_dmp.yaml")
        writer = DocxWriter(mapping=mapping, template_path=TEMPLATES_DIR / "cfa_template.docx")
        reader = DocxReader(mapping=mapping)

        output = tmp_path / "cfa_output.docx"
        writer.write(sample_dmp, output)
        recovered = reader.read(output)

        assert recovered.contact.name == "山田太郎"
        assert recovered.project[0].title == "サンプル研究プロジェクト"
        assert recovered.dataset[0].title == "実験データセット"
