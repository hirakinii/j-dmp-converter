"""Writer for CIR (Common Intermediate Representation) JSON files."""

from __future__ import annotations

from pathlib import Path

from adapters.writers.base import BaseWriter
from core.models import DMP, ValidationResult


class CirJsonWriter(BaseWriter):
    """Writes a CIR DMP to a JSON file."""

    def write(self, dmp: DMP, output_path: Path) -> Path:
        """Serialize the DMP model to a JSON file.

        Args:
            dmp: The CIR data model.
            output_path: Path for the output JSON file.

        Returns:
            The path of the written file.
        """
        text = dmp.model_dump_json(indent=2)
        output_path.write_text(text, encoding="utf-8")
        return output_path

    def validate(self, dmp: DMP) -> ValidationResult:
        """Validate the DMP for CIR JSON output.

        CIR is the canonical format, so any valid DMP instance is
        always complete. Validation always succeeds.

        Returns:
            A ValidationResult with is_complete=True.
        """
        return ValidationResult(is_complete=True)
