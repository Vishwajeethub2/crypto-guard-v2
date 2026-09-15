from pydantic import BaseModel


class CaseCreate(BaseModel):
    title: str
    description: str | None = None


class CaseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None