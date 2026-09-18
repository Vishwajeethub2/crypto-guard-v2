from datetime import datetime

from pydantic import BaseModel, Field


class CaseBookmarkCreate(BaseModel):
    bookmark_type: str = Field(
        min_length=1,
        max_length=50,
    )

    title: str = Field(
        min_length=1,
        max_length=255,
    )

    reference: str = Field(
        min_length=1,
        max_length=1000,
    )


class CaseBookmarkUpdate(BaseModel):
    bookmark_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    reference: str | None = Field(
        default=None,
        min_length=1,
        max_length=1000,
    )


class CaseBookmarkResponse(BaseModel):
    id: int
    case_id: int
    created_by: int
    bookmark_type: str
    title: str
    reference: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }