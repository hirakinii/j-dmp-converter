"""Tests for the conversion service."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from core.converter import ConversionService
from core.models import DMP, ValidationResult


class TestConversionService:
    def test_register_and_list_readers(self) -> None:
        service = ConversionService()
        reader = MagicMock()
        service.register_reader("amed", reader)
        assert "amed" in service.available_readers()

    def test_register_and_list_writers(self) -> None:
        service = ConversionService()
        writer = MagicMock()
        service.register_writer("jsps", writer)
        assert "jsps" in service.available_writers()

    def test_read_unknown_format_raises(self) -> None:
        service = ConversionService()
        with pytest.raises(ValueError, match="Unknown reader format"):
            service.read("unknown", Path("dummy.xlsx"))

    def test_write_unknown_format_raises(self, sample_dmp: DMP) -> None:
        service = ConversionService()
        with pytest.raises(ValueError, match="Unknown writer format"):
            service.write(sample_dmp, "unknown", Path("dummy.xlsx"))

    def test_validate_unknown_format_raises(self, sample_dmp: DMP) -> None:
        service = ConversionService()
        with pytest.raises(ValueError, match="Unknown writer format"):
            service.validate(sample_dmp, "unknown")

    def test_convert_returns_incomplete_when_fields_missing(self) -> None:
        service = ConversionService()

        mock_reader = MagicMock()
        mock_reader.read.return_value = MagicMock(spec=DMP)

        mock_writer = MagicMock()
        mock_writer.validate.return_value = ValidationResult(
            is_complete=False,
            missing_fields=[],
        )

        service.register_reader("amed", mock_reader)
        service.register_writer("jsps", mock_writer)

        output, result = service.convert("amed", "jsps", Path("in.xlsx"), Path("out.xlsx"))
        assert not result.is_complete
        mock_writer.write.assert_not_called()
