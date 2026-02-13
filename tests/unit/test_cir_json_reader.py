"""Tests for CIR JSON reader."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from adapters.readers.cir_json_reader import CirJsonReader
from core.models import DMP


class TestCirJsonReader:
    """Tests for CirJsonReader.read()."""

    def test_read_returns_dmp(self, sample_dmp: DMP, tmp_path: Path) -> None:
        """Reading a valid JSON file should return a DMP instance."""
        json_path = tmp_path / "dmp.json"
        json_path.write_text(
            sample_dmp.model_dump_json(indent=2), encoding="utf-8"
        )

        reader = CirJsonReader()
        result = reader.read(json_path)

        assert isinstance(result, DMP)

    def test_read_roundtrip_preserves_data(
        self, sample_dmp: DMP, tmp_path: Path
    ) -> None:
        """Data should survive a JSON serialization roundtrip."""
        json_path = tmp_path / "dmp.json"
        json_path.write_text(
            sample_dmp.model_dump_json(indent=2), encoding="utf-8"
        )

        reader = CirJsonReader()
        result = reader.read(json_path)

        assert result.title == sample_dmp.title
        assert result.dmp_id == sample_dmp.dmp_id
        assert result.language == sample_dmp.language
        assert result.contact.name == sample_dmp.contact.name
        assert len(result.dataset) == len(sample_dmp.dataset)
        assert result.dataset[0].title == sample_dmp.dataset[0].title

    def test_read_file_not_found(self, tmp_path: Path) -> None:
        """Reading a non-existent file should raise FileNotFoundError."""
        reader = CirJsonReader()

        with pytest.raises(FileNotFoundError):
            reader.read(tmp_path / "nonexistent.json")

    def test_read_invalid_json(self, tmp_path: Path) -> None:
        """Reading a file with invalid JSON should raise a ValidationError."""
        json_path = tmp_path / "bad.json"
        json_path.write_text("{invalid json", encoding="utf-8")

        reader = CirJsonReader()

        with pytest.raises(ValidationError):
            reader.read(json_path)

    def test_read_invalid_schema(self, tmp_path: Path) -> None:
        """Reading valid JSON that doesn't match the DMP schema should raise."""
        json_path = tmp_path / "wrong.json"
        json_path.write_text('{"not": "a dmp"}', encoding="utf-8")

        reader = CirJsonReader()

        with pytest.raises(Exception):
            reader.read(json_path)
