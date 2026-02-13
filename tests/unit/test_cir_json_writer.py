"""Tests for CIR JSON writer."""

from __future__ import annotations

import json
from pathlib import Path

from adapters.writers.cir_json_writer import CirJsonWriter
from core.models import DMP


class TestCirJsonWriter:
    """Tests for CirJsonWriter.write()."""

    def test_write_creates_file(self, sample_dmp: DMP, tmp_path: Path) -> None:
        """Writing a DMP should create a JSON file at the given path."""
        output_path = tmp_path / "output.json"

        writer = CirJsonWriter()
        result = writer.write(sample_dmp, output_path)

        assert result == output_path
        assert output_path.exists()

    def test_write_produces_valid_json(
        self, sample_dmp: DMP, tmp_path: Path
    ) -> None:
        """The written file should contain valid JSON."""
        output_path = tmp_path / "output.json"

        writer = CirJsonWriter()
        writer.write(sample_dmp, output_path)

        data = json.loads(output_path.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        assert data["title"] == sample_dmp.title

    def test_write_roundtrip(self, sample_dmp: DMP, tmp_path: Path) -> None:
        """A DMP written to JSON and read back should be equal."""
        output_path = tmp_path / "output.json"

        writer = CirJsonWriter()
        writer.write(sample_dmp, output_path)

        restored = DMP.model_validate_json(
            output_path.read_text(encoding="utf-8")
        )
        assert restored == sample_dmp

    def test_write_utf8_encoding(
        self, sample_dmp: DMP, tmp_path: Path
    ) -> None:
        """Japanese characters should be preserved (not escaped)."""
        output_path = tmp_path / "output.json"

        writer = CirJsonWriter()
        writer.write(sample_dmp, output_path)

        text = output_path.read_text(encoding="utf-8")
        assert "テスト用データマネジメントプラン" in text


class TestCirJsonWriterValidate:
    """Tests for CirJsonWriter.validate()."""

    def test_validate_always_complete(self, sample_dmp: DMP) -> None:
        """CIR is the canonical format so validation is always complete."""
        writer = CirJsonWriter()
        result = writer.validate(sample_dmp)

        assert result.is_complete is True
        assert result.missing_fields == []
