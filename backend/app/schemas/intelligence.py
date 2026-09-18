from pydantic import BaseModel, Field


class RiskEntityCreate(BaseModel):
    address: str
    chain: str = "ethereum"

    entity_type: str
    name: str
    source: str

    risk_category: str | None = None

    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    evidence: str | None = None
    updated_at: str | None = None

class RiskEntityUpdate(BaseModel):
    entity_type: str | None = None
    name: str | None = None
    source: str | None = None
    risk_category: str | None = None
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )
    evidence: str | None = None
    updated_at: str | None = None


class RiskEntityResponse(BaseModel):
    address: str
    chain: str

    entity_type: str
    name: str
    source: str

    risk_category: str | None = None
    confidence: float | None = None
    evidence: str | None = None
    updated_at: str | None = None