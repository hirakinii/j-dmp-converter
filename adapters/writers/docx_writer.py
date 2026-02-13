"""DOCX writer using docxtpl (Jinja2 for Word).

Renders CIR data into Word templates with Jinja2 placeholder tags.
"""

from __future__ import annotations

from pathlib import Path

from docxtpl import DocxTemplate

from adapters.mapping import MappingDefinition
from adapters.writers.base import BaseWriter
from core.models import DMP, MissingField, ValidationResult


class DocxWriter(BaseWriter):
    """Writes CIR data into a Word template file using docxtpl."""

    def __init__(self, mapping: MappingDefinition, template_path: Path) -> None:
        self._mapping = mapping
        self._template_path = template_path

    def write(self, dmp: DMP, output_path: Path) -> Path:
        """Inject CIR data into the Word template and save."""
        tpl = DocxTemplate(self._template_path)
        context = self._build_context(dmp)
        tpl.render(context)
        tpl.save(output_path)
        return output_path

    def validate(self, dmp: DMP) -> ValidationResult:
        """Check whether the DMP has all required fields for this format."""
        flat = self._flatten_dmp(dmp)
        missing: list[MissingField] = []

        for field_key, field_mapping in self._mapping.fields.items():
            if not field_mapping.required:
                continue
            value = flat.get(field_mapping.cir_path)
            if value is None or (isinstance(value, str) and value.strip() == ""):
                missing.append(
                    MissingField(
                        field_path=field_mapping.cir_path,
                        field_label=field_key,
                        required_by=self._mapping.format_id,
                    )
                )

        return ValidationResult(is_complete=len(missing) == 0, missing_fields=missing)

    def _build_context(self, dmp: DMP) -> dict[str, str]:
        """Build a docxtpl context dict from the DMP.

        Maps each YAML field key to its corresponding CIR value,
        using the field key as the Jinja2 template variable name.
        """
        flat = self._flatten_dmp(dmp)
        context: dict[str, str] = {}
        for field_key, field_mapping in self._mapping.fields.items():
            value = flat.get(field_mapping.cir_path)
            if value is not None:
                context[field_key] = value
            else:
                context[field_key] = ""
        return context

    def _flatten_dmp(self, dmp: DMP) -> dict[str, str | None]:
        """Flatten the nested DMP structure into dot-path keyed values."""
        flat: dict[str, str | None] = {}
        data = dmp.model_dump(mode="json")
        self._flatten_dict(data, "", flat)
        return flat

    def _flatten_dict(
        self, obj: dict | list | object, prefix: str, result: dict[str, str | None]
    ) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_key = f"{prefix}.{key}" if prefix else key
                self._flatten_dict(value, new_key, result)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                new_key = f"{prefix}.{i}"
                self._flatten_dict(item, new_key, result)
        else:
            result[prefix] = str(obj) if obj is not None else None
