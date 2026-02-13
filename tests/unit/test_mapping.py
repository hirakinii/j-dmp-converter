"""Tests for mapping definition loader."""

from __future__ import annotations

from pathlib import Path

from adapters.mapping import load_mapping

DEFINITIONS_DIR = Path(__file__).resolve().parent.parent.parent / "adapters" / "definitions"


class TestLoadMapping:
    def test_load_amed_mapping(self) -> None:
        mapping = load_mapping(DEFINITIONS_DIR / "amed_dmp.yaml")
        assert mapping.format_id == "amed"
        assert mapping.file_type == "xlsx"
        assert "project_title" in mapping.fields
        assert mapping.fields["project_title"].cir_path == "project.0.title"
        assert mapping.fields["project_title"].excel_cell == "D8"
        assert mapping.fields["project_title"].excel_sheet == "DMP様式"
        assert mapping.fields["project_title"].required is True

    def test_load_jsps_mapping(self) -> None:
        mapping = load_mapping(DEFINITIONS_DIR / "jsps_dmp.yaml")
        assert mapping.format_id == "jsps"
        assert mapping.file_type == "xlsx"
        assert "erad_project_id" in mapping.fields
        assert mapping.fields["erad_project_id"].excel_cell == "C9"
        assert mapping.fields["erad_project_id"].required is True

    def test_load_meti_mapping(self) -> None:
        mapping = load_mapping(DEFINITIONS_DIR / "meti_dmp.yaml")
        assert mapping.format_id == "meti"
        assert mapping.file_type == "xlsx"
        assert "project_title" in mapping.fields
        assert mapping.fields["project_title"].excel_cell == "D5"
        assert mapping.fields["project_title"].required is True

    def test_amed_has_fewer_required_fields_than_jsps(self) -> None:
        """AMED typically requires fewer fields than JSPS."""
        amed = load_mapping(DEFINITIONS_DIR / "amed_dmp.yaml")
        jsps = load_mapping(DEFINITIONS_DIR / "jsps_dmp.yaml")

        amed_required = [f for f in amed.fields.values() if f.required]
        jsps_required = [f for f in jsps.fields.values() if f.required]

        assert len(amed_required) < len(jsps_required)

    def test_all_mappings_have_dataset_title(self) -> None:
        """All format mappings should include a dataset title field."""
        for name in ["amed_dmp.yaml", "jsps_dmp.yaml", "meti_dmp.yaml"]:
            mapping = load_mapping(DEFINITIONS_DIR / name)
            assert "dataset_title" in mapping.fields, f"{name} missing dataset_title"
