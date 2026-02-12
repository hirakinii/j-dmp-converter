"""Common Intermediate Representation (CIR) data models.

Based on the RDA DMP Common Standard (maDMP) with extensions for
Japanese funding agency requirements (e-Rad, J-Global, etc.).
"""

from __future__ import annotations

import enum
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class DataAccess(str, enum.Enum):
    OPEN = "open"
    SHARED = "shared"
    CLOSED = "closed"


class Booleanish(str, enum.Enum):
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"


class FundingStatus(str, enum.Enum):
    PLANNED = "planned"
    APPLIED = "applied"
    GRANTED = "granted"
    REJECTED = "rejected"


class Certification(str, enum.Enum):
    DIN31644 = "din31644"
    DINI_ZERTIFIKAT = "dini-zertifikat"
    DSA = "dsa"
    ISO16363 = "iso16363"
    ISO16919 = "iso16919"
    TRAC = "trac"
    WDS = "wds"
    CORETRUSTSEAL = "coretrustseal"


# ---------------------------------------------------------------------------
# Identifier models
# ---------------------------------------------------------------------------


class TypedIdentifier(BaseModel):
    """Generic typed identifier used across the schema."""

    identifier: str
    type: str


# ---------------------------------------------------------------------------
# Shared sub-models
# ---------------------------------------------------------------------------


class Affiliation(BaseModel):
    affiliation_id: TypedIdentifier | None = None
    name: str


class Contact(BaseModel):
    """Party that can provide information about the DMP."""

    contact_id: TypedIdentifier | list[TypedIdentifier]
    mbox: EmailStr
    name: str
    affiliation: list[Affiliation] = Field(default_factory=list)


class Contributor(BaseModel):
    contributor_id: TypedIdentifier | list[TypedIdentifier]
    name: str
    role: list[str] = Field(default_factory=list)
    mbox: EmailStr | None = None
    affiliation: list[Affiliation] = Field(default_factory=list)

    # --- Japan extensions ---
    erad_researcher_id: str | None = Field(
        default=None, description="e-Rad researcher number (e-Rad研究者番号)"
    )
    institution_code: str | None = Field(
        default=None, description="Institutional code (所属機関コード)"
    )


class Creator(BaseModel):
    creator_id: TypedIdentifier | list[TypedIdentifier]
    name: str
    mbox: EmailStr | None = None
    affiliation: list[Affiliation] = Field(default_factory=list)


class AlternateIdentifier(BaseModel):
    identifier: str
    type: str


class RelatedIdentifier(BaseModel):
    identifier: str
    type: str
    relation_type: str
    metadata_scheme: str | None = None
    resource_type: str | None = None
    scheme_type: str | None = None
    scheme_uri: str | None = None


# ---------------------------------------------------------------------------
# Cost
# ---------------------------------------------------------------------------


class Cost(BaseModel):
    title: str
    description: str | None = None
    value: float | None = None
    currency_code: str | None = Field(default=None, description="ISO 4217 currency code")


# ---------------------------------------------------------------------------
# Funding / Project
# ---------------------------------------------------------------------------


class FunderID(BaseModel):
    identifier: str
    type: str


class GrantID(BaseModel):
    identifier: str
    type: str


class Funding(BaseModel):
    funder_id: FunderID
    funding_status: FundingStatus | None = None
    grant_id: GrantID | None = None


class Project(BaseModel):
    title: str
    description: str | None = None
    start: date | None = None
    end: date | None = None
    funding: list[Funding] = Field(default_factory=list)
    project_id: list[TypedIdentifier] = Field(default_factory=list)

    # --- Japan extensions ---
    erad_project_id: str | None = Field(
        default=None, description="e-Rad project ID (e-Rad課題ID)"
    )
    jglobal_id: str | None = Field(
        default=None, description="J-Global ID"
    )


# ---------------------------------------------------------------------------
# Host / License / Distribution
# ---------------------------------------------------------------------------


class Host(BaseModel):
    title: str
    url: str
    description: str | None = None
    availability: str | None = None
    backup_frequency: str | None = None
    backup_type: str | None = None
    certified_with: Certification | None = None
    geo_location: str | None = Field(default=None, description="ISO 3166-1 country code")
    host_id: list[TypedIdentifier] = Field(default_factory=list)
    pid_system: list[str] = Field(default_factory=list)
    storage_type: str | None = None
    support_versioning: Booleanish | None = None


class License(BaseModel):
    license_ref: str
    start_date: date


class Distribution(BaseModel):
    title: str
    data_access: DataAccess
    access_url: str | None = None
    available_until: date | None = None
    byte_size: int | None = None
    description: str | None = None
    download_url: str | None = None
    format: list[str] = Field(default_factory=list)
    host: Host | None = None
    issued: date | None = None
    license: list[License] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Metadata / Security / Technical Resource
# ---------------------------------------------------------------------------


class MetadataStandardID(BaseModel):
    identifier: str
    type: str


class Metadata(BaseModel):
    language: str = Field(description="ISO 639-3 language code")
    metadata_standard_id: MetadataStandardID | list[MetadataStandardID]
    description: str | None = None


class SecurityAndPrivacy(BaseModel):
    title: str
    description: str | None = None


class TechnicalResource(BaseModel):
    name: str
    description: str | None = None
    technical_resource_id: list[TypedIdentifier] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------


class Dataset(BaseModel):
    title: str
    dataset_id: TypedIdentifier
    personal_data: Booleanish
    sensitive_data: Booleanish
    description: str | None = None
    type: str | None = None
    issued: date | None = None
    language: str | None = Field(default=None, description="ISO 639-3 language code")
    is_reused: bool | None = None
    keyword: list[str] = Field(default_factory=list)
    alternate_identifier: list[AlternateIdentifier] = Field(default_factory=list)
    creator: list[Creator] = Field(default_factory=list)
    distribution: list[Distribution] = Field(default_factory=list)
    metadata: list[Metadata] = Field(default_factory=list)
    related_identifier: list[RelatedIdentifier] = Field(default_factory=list)
    security_and_privacy: list[SecurityAndPrivacy] = Field(default_factory=list)
    technical_resource: list[TechnicalResource] = Field(default_factory=list)
    data_quality_assurance: list[str] = Field(default_factory=list)
    preservation_statement: str | None = None
    rights: str | None = None


# ---------------------------------------------------------------------------
# DMP (root)
# ---------------------------------------------------------------------------


class DMP(BaseModel):
    """Root model for the Common Intermediate Representation (CIR).

    Based on the RDA DMP Common Standard with Japanese extensions.
    """

    title: str
    dmp_id: TypedIdentifier
    created: datetime
    modified: datetime
    language: str = Field(description="ISO 639-3 language code")
    ethical_issues_exist: Booleanish
    contact: Contact
    dataset: list[Dataset] = Field(min_length=1)

    description: str | None = None
    ethical_issues_description: str | None = None
    ethical_issues_report: str | None = None
    contributor: list[Contributor] = Field(default_factory=list)
    cost: list[Cost] = Field(default_factory=list)
    project: list[Project] = Field(default_factory=list)
    alternate_identifier: list[AlternateIdentifier] = Field(default_factory=list)
    related_identifier: list[RelatedIdentifier] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Validation result (for gap analysis)
# ---------------------------------------------------------------------------


class MissingField(BaseModel):
    """A field required by the target format but missing from the CIR."""

    field_path: str = Field(description="Dot-separated path, e.g. 'project.0.erad_project_id'")
    field_label: str = Field(description="Human-readable label for UI display")
    required_by: str = Field(description="Target agency format that requires this field")


class ValidationResult(BaseModel):
    """Result of gap analysis between CIR data and target format requirements."""

    is_complete: bool
    missing_fields: list[MissingField] = Field(default_factory=list)
