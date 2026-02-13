"""Conversion orchestration logic.

Coordinates the Reader -> CIR -> Writer pipeline and performs
gap analysis between source and target formats.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from core.models import DMP, MissingField, ValidationResult

if TYPE_CHECKING:
    from adapters.readers.base import BaseReader
    from adapters.writers.base import BaseWriter


class ConversionService:
    """Orchestrates the full conversion pipeline.

    Usage::

        service = ConversionService()
        cir = service.read("amed", Path("input.xlsx"))
        result = service.validate(cir, target_format="jsps")
        if result.is_complete:
            service.write(cir, "jsps", Path("output.xlsx"))
    """

    def __init__(self) -> None:
        self._readers: dict[str, BaseReader] = {}
        self._writers: dict[str, BaseWriter] = {}

    # -- Registry ----------------------------------------------------------

    def register_reader(self, format_id: str, reader: BaseReader) -> None:
        """Register a reader for the given format.

        Args:
            format_id: Format identifier string (e.g. "amed").
            reader: BaseReader implementation to register.
        """
        self._readers[format_id] = reader

    def register_writer(self, format_id: str, writer: BaseWriter) -> None:
        """Register a writer for the given format.

        Args:
            format_id: Format identifier string (e.g. "jsps").
            writer: BaseWriter implementation to register.
        """
        self._writers[format_id] = writer

    def available_readers(self) -> list[str]:
        """Return a list of registered reader format IDs."""
        return list(self._readers.keys())

    def available_writers(self) -> list[str]:
        """Return a list of registered writer format IDs."""
        return list(self._writers.keys())

    # -- Pipeline ----------------------------------------------------------

    def read(self, format_id: str, input_path: Path) -> DMP:
        """Read an agency file and convert it to CIR."""
        reader = self._readers.get(format_id)
        if reader is None:
            raise ValueError(f"Unknown reader format: {format_id}")
        return reader.read(input_path)

    def write(self, dmp: DMP, format_id: str, output_path: Path) -> Path:
        """Write CIR data to the target agency format."""
        writer = self._writers.get(format_id)
        if writer is None:
            raise ValueError(f"Unknown writer format: {format_id}")
        return writer.write(dmp, output_path)

    def validate(self, dmp: DMP, target_format: str) -> ValidationResult:
        """Perform gap analysis between CIR data and target format requirements.

        Returns a ValidationResult indicating whether all required fields for
        the target format are present, along with a list of any missing fields.
        """
        writer = self._writers.get(target_format)
        if writer is None:
            raise ValueError(f"Unknown writer format: {target_format}")
        return writer.validate(dmp)

    def convert(
        self,
        source_format: str,
        target_format: str,
        input_path: Path,
        output_path: Path,
    ) -> tuple[Path, ValidationResult]:
        """Full pipeline: read source -> validate -> write target.

        Returns the output path and validation result.
        Raises ValueError if required fields are missing in the CIR.
        """
        dmp = self.read(source_format, input_path)
        result = self.validate(dmp, target_format)
        if not result.is_complete:
            return output_path, result
        written = self.write(dmp, target_format, output_path)
        return written, result
