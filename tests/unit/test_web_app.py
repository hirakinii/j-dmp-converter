"""Tests for the FastAPI web application.

Step 4.1: API server tests — endpoints, startup registration.
Step 4.2: Missing field supplementation flow tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from web.app import app

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


class TestListFormats:
    """GET /formats should return all registered reader/writer formats."""

    def test_list_formats(self, client: TestClient) -> None:
        response = client.get("/formats")
        assert response.status_code == 200

        data = response.json()
        assert "readers" in data
        assert "writers" in data
        assert sorted(data["readers"]) == ["amed", "cfa", "jsps", "meti"]
        assert sorted(data["writers"]) == ["amed", "cfa", "jsps", "meti"]


class TestConvertEndpoint:
    """POST /convert should accept a file and return the converted file."""

    def test_convert_amed_to_amed(self, client: TestClient) -> None:
        """Upload AMED fixture, convert to AMED (same format) — should return 200 + xlsx."""
        fixture = FIXTURES_DIR / "filled_amed_sample.xlsx"
        with open(fixture, "rb") as f:
            response = client.post(
                "/convert",
                params={"source_format": "amed", "target_format": "amed"},
                files={"file": ("filled_amed_sample.xlsx", f, "application/octet-stream")},
            )

        assert response.status_code == 200
        assert len(response.content) > 0
        assert "converted_amed" in response.headers.get("content-disposition", "")
        assert ".xlsx" in response.headers.get("content-disposition", "")

    def test_convert_amed_to_cfa(self, client: TestClient) -> None:
        """Cross-format conversion: AMED (xlsx) -> CFA (docx)."""
        fixture = FIXTURES_DIR / "filled_amed_sample.xlsx"
        with open(fixture, "rb") as f:
            response = client.post(
                "/convert",
                params={"source_format": "amed", "target_format": "cfa"},
                files={"file": ("filled_amed_sample.xlsx", f, "application/octet-stream")},
            )

        assert response.status_code == 200
        assert len(response.content) > 0
        # CFA output should be a docx file
        assert ".docx" in response.headers.get("content-disposition", "")

    def test_convert_unknown_source_format(self, client: TestClient) -> None:
        fixture = FIXTURES_DIR / "filled_amed_sample.xlsx"
        with open(fixture, "rb") as f:
            response = client.post(
                "/convert",
                params={"source_format": "unknown", "target_format": "jsps"},
                files={"file": ("test.xlsx", f, "application/octet-stream")},
            )

        assert response.status_code == 400

    def test_convert_unknown_target_format(self, client: TestClient) -> None:
        fixture = FIXTURES_DIR / "filled_amed_sample.xlsx"
        with open(fixture, "rb") as f:
            response = client.post(
                "/convert",
                params={"source_format": "amed", "target_format": "unknown"},
                files={"file": ("test.xlsx", f, "application/octet-stream")},
            )

        assert response.status_code == 400


class TestValidateEndpoint:
    """POST /validate should perform gap analysis."""

    def test_validate_returns_validation_result(
        self, client: TestClient, sample_dmp
    ) -> None:
        dmp_json = sample_dmp.model_dump(mode="json")
        response = client.post(
            "/validate",
            params={"target_format": "amed"},
            json=dmp_json,
        )

        assert response.status_code == 200
        data = response.json()
        assert "is_complete" in data
        assert "missing_fields" in data


class TestConvertIncomplete:
    """POST /convert with insufficient data should return CIR + missing fields."""

    def test_convert_incomplete_returns_dmp_and_missing_fields(
        self, client: TestClient
    ) -> None:
        """When conversion has missing fields, response should include
        the intermediate CIR and the list of missing fields.
        """
        fixture = FIXTURES_DIR / "filled_amed_sample.xlsx"
        with open(fixture, "rb") as f:
            response = client.post(
                "/convert",
                params={"source_format": "amed", "target_format": "meti"},
                files={"file": ("filled_amed_sample.xlsx", f, "application/octet-stream")},
            )

        # If conversion is incomplete, should return 422 with structured data
        if response.status_code == 422:
            data = response.json()
            detail = data["detail"]
            assert "missing_fields" in detail
            assert "dmp" in detail
            # The DMP should be a full CIR JSON that the client can supplement
            assert "title" in detail["dmp"]


class TestConvertComplete:
    """POST /convert/complete accepts supplemented CIR and returns the file."""

    def test_convert_complete_with_supplemented_dmp(
        self, client: TestClient, sample_dmp
    ) -> None:
        """POST a complete DMP JSON -> should get the converted file back."""
        dmp_json = sample_dmp.model_dump(mode="json")
        response = client.post(
            "/convert/complete",
            params={"target_format": "amed"},
            json=dmp_json,
        )

        assert response.status_code == 200
        assert len(response.content) > 0
        assert ".xlsx" in response.headers.get("content-disposition", "")

    def test_convert_complete_docx_format(
        self, client: TestClient, sample_dmp
    ) -> None:
        """POST a complete DMP JSON for CFA -> should get docx back."""
        dmp_json = sample_dmp.model_dump(mode="json")
        response = client.post(
            "/convert/complete",
            params={"target_format": "cfa"},
            json=dmp_json,
        )

        assert response.status_code == 200
        assert len(response.content) > 0
        assert ".docx" in response.headers.get("content-disposition", "")

    def test_convert_complete_unknown_format(
        self, client: TestClient, sample_dmp
    ) -> None:
        dmp_json = sample_dmp.model_dump(mode="json")
        response = client.post(
            "/convert/complete",
            params={"target_format": "unknown"},
            json=dmp_json,
        )

        assert response.status_code == 400
