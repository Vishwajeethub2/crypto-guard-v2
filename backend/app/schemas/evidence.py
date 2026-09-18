from datetime import datetime

from pydantic import BaseModel, Field


class CaseEvidenceCreate(BaseModel):
    evidence_type: str = Field(
        min_length=1,
        max_length=50,
    )

    title: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=10000,
    )

    reference: str | None = Field(
        default=None,
        max_length=1000,
    )


class CaseEvidenceUpdate(BaseModel):
    evidence_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=10000,
    )

    reference: str | None = Field(
        default=None,
        max_length=1000,
    )


class CaseEvidenceResponse(BaseModel):
    id: int
    case_id: int
    created_by: int
    evidence_type: str
    title: str
    description: str | None
    reference: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }