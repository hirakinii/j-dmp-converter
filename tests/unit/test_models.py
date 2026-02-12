"""Tests for CIR schema validation (Step 1.1 of implementation plan)."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from core.models import (
    Booleanish,
    Contact,
    DataAccess,
    Dataset,
    Distribution,
    DMP,
    MissingField,
    Project,
    TypedIdentifier,
    ValidationResult,
)


class TestDMPValidation:
    """Test that CIR schema correctly validates and rejects data."""

    def test_valid_dmp_is_accepted(self, sample_dmp: DMP) -> None:
        """A complete DMP should pass validation."""
        assert sample_dmp.title == "テスト用データマネジメントプラン"
        assert sample_dmp.language == "jpn"
        assert len(sample_dmp.dataset) == 1

    def test_missing_title_is_rejected(self) -> None:
        """DMP without a title should fail validation."""
        with pytest.raises(ValidationError):
            DMP(
                # title is missing
                dmp_id=TypedIdentifier(identifier="test", type="url"),
                created=datetime.now(timezone.utc),
                modified=datetime.now(timezone.utc),
                language="jpn",
                ethical_issues_exist=Booleanish.NO,
                contact=Contact(
                    contact_id=TypedIdentifier(identifier="test", type="orcid"),
                    mbox="test@example.com",
                    name="Test",
                ),
                dataset=[
                    Dataset(
                        title="ds",
                        dataset_id=TypedIdentifier(identifier="ds1", type="url"),
                        personal_data=Booleanish.NO,
                        sensitive_data=Booleanish.NO,
                    )
                ],
            )

    def test_missing_contact_is_rejected(self) -> None:
        """DMP without contact info should fail validation."""
        with pytest.raises(ValidationError):
            DMP(
                title="Test DMP",
                dmp_id=TypedIdentifier(identifier="test", type="url"),
                created=datetime.now(timezone.utc),
                modified=datetime.now(timezone.utc),
                language="jpn",
                ethical_issues_exist=Booleanish.NO,
                # contact is missing
                dataset=[
                    Dataset(
                        title="ds",
                        dataset_id=TypedIdentifier(identifier="ds1", type="url"),
                        personal_data=Booleanish.NO,
                        sensitive_data=Booleanish.NO,
                    )
                ],
            )

    def test_empty_dataset_list_is_rejected(self) -> None:
        """DMP must contain at least one dataset."""
        with pytest.raises(ValidationError):
            DMP(
                title="Test DMP",
                dmp_id=TypedIdentifier(identifier="test", type="url"),
                created=datetime.now(timezone.utc),
                modified=datetime.now(timezone.utc),
                language="jpn",
                ethical_issues_exist=Booleanish.NO,
                contact=Contact(
                    contact_id=TypedIdentifier(identifier="test", type="orcid"),
                    mbox="test@example.com",
                    name="Test",
                ),
                dataset=[],  # Empty dataset list
            )

    def test_invalid_data_access_is_rejected(self) -> None:
        """Distribution with invalid data_access value should fail."""
        with pytest.raises(ValidationError):
            Distribution(
                title="test",
                data_access="invalid_value",  # type: ignore[arg-type]
            )

    def test_valid_data_access_values(self) -> None:
        """All valid DataAccess enum values should be accepted."""
        for access in DataAccess:
            dist = Distribution(title="test", data_access=access)
            assert dist.data_access == access


class TestJapanExtensions:
    """Test Japan-specific extension fields."""

    def test_project_with_erad_id(self) -> None:
        project = Project(title="Test", erad_project_id="JP26000001")
        assert project.erad_project_id == "JP26000001"

    def test_project_with_jglobal_id(self) -> None:
        project = Project(title="Test", jglobal_id="202001234567")
        assert project.jglobal_id == "202001234567"

    def test_project_without_japan_extensions(self) -> None:
        project = Project(title="Test")
        assert project.erad_project_id is None
        assert project.jglobal_id is None


class TestDMPSerialization:
    """Test JSON serialization / deserialization round-trip."""

    def test_round_trip(self, sample_dmp: DMP) -> None:
        """Serializing and deserializing should produce equivalent data."""
        json_str = sample_dmp.model_dump_json()
        restored = DMP.model_validate_json(json_str)
        assert restored.title == sample_dmp.title
        assert restored.contact.name == sample_dmp.contact.name
        assert len(restored.dataset) == len(sample_dmp.dataset)
        assert restored.project[0].erad_project_id == sample_dmp.project[0].erad_project_id


class TestValidationResult:
    """Test gap analysis models."""

    def test_complete_result(self) -> None:
        result = ValidationResult(is_complete=True)
        assert result.is_complete
        assert result.missing_fields == []

    def test_incomplete_result(self) -> None:
        result = ValidationResult(
            is_complete=False,
            missing_fields=[
                MissingField(
                    field_path="project.0.erad_project_id",
                    field_label="e-Rad課題ID",
                    required_by="jsps",
                ),
            ],
        )
        assert not result.is_complete
        assert len(result.missing_fields) == 1
        assert result.missing_fields[0].required_by == "jsps"
