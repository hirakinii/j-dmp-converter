"""Shared test fixtures for J DMP Converter."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from core.models import (
    DMP,
    Affiliation,
    Booleanish,
    Contact,
    Contributor,
    DataAccess,
    Dataset,
    Distribution,
    Host,
    License,
    Project,
    TypedIdentifier,
)


@pytest.fixture
def sample_dmp() -> DMP:
    """Create a minimal but complete DMP for testing."""
    return DMP(
        title="テスト用データマネジメントプラン",
        dmp_id=TypedIdentifier(identifier="https://example.org/dmp/001", type="url"),
        created=datetime(2026, 4, 1, 0, 0, 0, tzinfo=timezone.utc),
        modified=datetime(2026, 4, 1, 0, 0, 0, tzinfo=timezone.utc),
        language="jpn",
        ethical_issues_exist=Booleanish.NO,
        contact=Contact(
            contact_id=TypedIdentifier(
                identifier="0000-0001-2345-6789", type="orcid"
            ),
            mbox="yamada@example.ac.jp",
            name="山田太郎",
            affiliation=[
                Affiliation(
                    affiliation_id=TypedIdentifier(identifier="1234567890", type="ror"),
                    name="東京大学",
                ),
            ],
        ),
        contributor=[
            Contributor(
                contributor_id=TypedIdentifier(
                    identifier="0000-0001-2345-6789", type="orcid"
                ),
                name="山田太郎",
                role=["DataManager", "Researcher"],
                erad_researcher_id="12345678",
            ),
        ],
        project=[
            Project(
                title="サンプル研究プロジェクト",
                description="データマネジメントプランのコンバーターに関する研究",
                start=date(2026, 4, 1),
                end=date(2029, 3, 31),
                erad_project_id="JP26000001",
            ),
        ],
        dataset=[
            Dataset(
                title="実験データセット",
                dataset_id=TypedIdentifier(
                    identifier="https://example.org/dataset/001", type="url"
                ),
                personal_data=Booleanish.NO,
                sensitive_data=Booleanish.NO,
                description="サンプル実験データ",
                type="dataset",
                language="jpn",
                keyword=["テスト", "サンプル"],
                distribution=[
                    Distribution(
                        title="実験データ配布",
                        data_access=DataAccess.OPEN,
                        format=["text/csv"],
                        host=Host(
                            title="機関リポジトリ",
                            url="https://repository.example.ac.jp",
                        ),
                        license=[
                            License(
                                license_ref="https://creativecommons.org/licenses/by/4.0/",
                                start_date=date(2029, 4, 1),
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )
