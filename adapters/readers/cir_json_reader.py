"""Reader for CIR (Common Intermediate Representation) JSON files."""

from __future__ import annotations

from pathlib import Path

from adapters.readers.base import BaseReader
from core.models import DMP


class CirJsonReader(BaseReader):
    """Reads a CIR DMP from a JSON file."""

    def read(self, input_path: Path) -> DMP:
        """Read a CIR JSON file and return the DMP model.

        Args:
            input_path: Path to the JSON file.

        Returns:
            A DMP model populated from the JSON data.

        Raises:
            FileNotFoundError: If the input file does not exist.
            json.JSONDecodeError: If the file contains invalid JSON.
            pydantic.ValidationError: If the JSON does not match the DMP schema.
        """
        text = input_path.read_text(encoding="utf-8")
        return DMP.model_validate_json(text)
