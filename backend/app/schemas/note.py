from datetime import datetime

from pydantic import BaseModel, Field


class CaseNoteCreate(BaseModel):
    content: str = Field(
        min_length=1,
        max_length=10000,
    )


class CaseNoteUpdate(BaseModel):
    content: str = Field(
        min_length=1,
        max_length=10000,
    )


class CaseNoteResponse(BaseModel):
    id: int
    case_id: int
    created_by: int
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }