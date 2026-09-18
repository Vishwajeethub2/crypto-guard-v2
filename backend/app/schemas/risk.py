from typing import Any, Literal

from pydantic import BaseModel, Field


SeverityLevel = Literal[
    "low",
    "medium",
    "high",
    "critical",
]


RiskLevel = Literal[
    "low",
    "moderate",
    "high",
    "critical",
]


class WalletBehaviorResponse(BaseModel):
    address: str
    chain: str

    outgoing_connections: int
    incoming_connections: int
    total_connections: int

    outgoing_transaction_count: int
    incoming_transaction_count: int
    total_transaction_count: int

    outgoing_value: float
    incoming_value: float

    unique_assets: int


class RiskIndicatorResponse(BaseModel):
    indicator: str
    severity: SeverityLevel
    reason: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class SeverityCountsResponse(BaseModel):
    low: int
    medium: int
    high: int
    critical: int


class RiskTransferEvidence(BaseModel):
    transaction_hash: str
    asset: str | None = None
    value: float | None = None
    category: str | None = None
    block_number: int | None = None
    timestamp: str | None = None
    contract_address: str | None = None


class RiskExposureResponse(BaseModel):
    risk_entity_address: str
    risk_entity_chain: str
    entity_type: str
    entity_name: str | None = None
    source: str | None = None

    risk_category: str | None = None
    confidence: float | None = None
    evidence: str | None = None
    updated_at: str | None = None

    wallets: list[str]
    transfers: list[RiskTransferEvidence]
    hop_count: int


class WalletRiskAnalysisResponse(BaseModel):
    address: str
    chain: str

    risk_score: int = Field(
        ge=0,
        le=100,
    )

    risk_level: RiskLevel

    indicator_count: int
    exposure_count: int

    severity_counts: SeverityCountsResponse

    behavior: WalletBehaviorResponse | None = None

    indicators: list[RiskIndicatorResponse]

    exposures: list[RiskExposureResponse]

class AdvancedRiskFactorResponse(BaseModel):
    factor: str
    contribution: int
    reason: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class AdvancedRiskResponse(BaseModel):
    address: str
    chain: str
    risk_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    factors: list[AdvancedRiskFactorResponse]
    behavior: WalletBehaviorResponse | None = None
    exposures: list[RiskExposureResponse]