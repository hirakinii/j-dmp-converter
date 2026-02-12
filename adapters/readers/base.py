"""Base reader interface for all format-specific readers."""

from __future__ import annotations

import abc
from pathlib import Path

from core.models import DMP


class BaseReader(abc.ABC):
    """Abstract base class for file readers (importers).

    Each funding agency format should implement a concrete reader that
    parses the agency-specific file and converts it to a CIR DMP model.
    """

    @abc.abstractmethod
    def read(self, input_path: Path) -> DMP:
        """Read a file and return the CIR representation.

        Args:
            input_path: Path to the input file (Excel or Word).

        Returns:
            A DMP model populated with data from the file.
        """
