"""Base writer interface for all format-specific writers."""

from __future__ import annotations

import abc
from pathlib import Path

from core.models import DMP, ValidationResult


class BaseWriter(abc.ABC):
    """Abstract base class for file writers (exporters).

    Each funding agency format should implement a concrete writer that
    injects CIR data into the agency-specific template file.
    """

    @abc.abstractmethod
    def write(self, dmp: DMP, output_path: Path) -> Path:
        """Write CIR data to the target format.

        Args:
            dmp: The CIR data model.
            output_path: Path for the output file.

        Returns:
            The actual path of the written file.
        """

    @abc.abstractmethod
    def validate(self, dmp: DMP) -> ValidationResult:
        """Check whether the DMP contains all fields required by this format.

        Returns:
            A ValidationResult with any missing fields listed.
        """
