from pydantic import BaseModel


class CaseCreate(BaseModel):
    title: str
    description: str | None = None