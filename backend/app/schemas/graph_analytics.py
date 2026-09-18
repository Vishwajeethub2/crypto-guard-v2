from typing import Any

from pydantic import BaseModel, Field


class GraphCounterpartyResponse(BaseModel):
    address: str
    chain: str = "ethereum"
    transaction_count: int
    total_value: float


class GraphRiskPathResponse(BaseModel):
    risk_entity_address: str
    risk_entity_chain: str
    entity_type: str
    entity_name: str | None = None
    hop_count: int
    wallets: list[str]
    transfers: list[dict[str, Any]]


class GraphAnalyticsResponse(BaseModel):
    address: str
    chain: str

    outgoing_connections: int
    incoming_connections: int

    outgoing_transaction_count: int
    incoming_transaction_count: int

    outgoing_value: float
    incoming_value: float

    fan_out: int
    fan_in: int

    top_outgoing_counterparties: list[GraphCounterpartyResponse]
    top_incoming_counterparties: list[GraphCounterpartyResponse]

    outgoing_concentration: float = Field(
        ge=0.0,
        le=1.0,
    )

    incoming_concentration: float = Field(
        ge=0.0,
        le=1.0,
    )

    multi_hop_risk_paths: list[GraphRiskPathResponse]
    multi_hop_exposure_count: int

    graph_signals: list[dict[str, Any]]