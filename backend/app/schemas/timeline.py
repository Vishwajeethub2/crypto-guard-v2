from typing import Any

from pydantic import BaseModel, Field


class TimelineTransactionResponse(BaseModel):
    transaction_hash: str
    chain: str
    direction: str
    counterparty: str
    asset: str | None = None
    value: float
    block_number: int | None = None
    timestamp: str | None = None
    contract_address: str | None = None


class TimelineBurstResponse(BaseModel):
    start_time: str
    end_time: str
    transaction_count: int
    duration_seconds: float


class TimelineAnalyticsResponse(BaseModel):
    address: str
    chain: str

    first_activity: str | None = None
    last_activity: str | None = None

    total_transactions: int
    incoming_transactions: int
    outgoing_transactions: int

    incoming_value: float
    outgoing_value: float
    total_value: float

    activity_duration_seconds: float
    average_transaction_gap_seconds: float | None = None

    shortest_transaction_gap_seconds: float | None = None
    longest_transaction_gap_seconds: float | None = None

    bursts: list[TimelineBurstResponse]

    largest_transactions: list[TimelineTransactionResponse]

    transactions: list[TimelineTransactionResponse]

    temporal_signals: list[dict[str, Any]]