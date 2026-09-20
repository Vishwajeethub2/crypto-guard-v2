from __future__ import annotations

from typing import Any


def safe_divide(
    numerator: float,
    denominator: float,
) -> float:
    if denominator == 0:
        return 0.0

    return numerator / denominator


def calculate_concentration(
    values: list[float],
) -> float:
    positive_values = [
        float(value)
        for value in values
        if float(value) > 0
    ]

    total = sum(positive_values)

    if total <= 0:
        return 0.0

    return sum(
        (value / total) ** 2
        for value in positive_values
    )


def _get_numeric(
    data: dict[str, Any],
    key: str,
    default: float = 0.0,
) -> float:
    value = data.get(key, default)

    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def build_ml_features(
    behavior: dict[str, Any],
    graph: dict[str, Any],
    timeline: dict[str, Any],
) -> dict[str, float]:
    """
    Convert existing Crypto Guard analytical results into
    the standardized ML feature schema.

    This function intentionally does not call Alchemy.
    It operates on data already available to Crypto Guard.
    """

    # ------------------------------------------------------------
    # Transaction activity
    # ------------------------------------------------------------

    incoming_transactions = _get_numeric(
        behavior,
        "incoming_transaction_count",
        graph.get(
            "incoming_transaction_count",
            0,
        ),
    )

    outgoing_transactions = _get_numeric(
        behavior,
        "outgoing_transaction_count",
        graph.get(
            "outgoing_transaction_count",
            0,
        ),
    )

    transaction_count = (
        incoming_transactions
        + outgoing_transactions
    )

    unique_incoming = _get_numeric(
        graph,
        "incoming_connections",
    )

    unique_outgoing = _get_numeric(
        graph,
        "outgoing_connections",
    )

    activity_duration = _get_numeric(
        timeline,
        "activity_duration_seconds",
    )

    # ------------------------------------------------------------
    # Value flow
    # ------------------------------------------------------------

    incoming_value = _get_numeric(
        behavior,
        "incoming_value",
        graph.get(
            "incoming_value",
            0,
        ),
    )

    outgoing_value = _get_numeric(
        behavior,
        "outgoing_value",
        graph.get(
            "outgoing_value",
            0,
        ),
    )

    average_incoming = safe_divide(
        incoming_value,
        incoming_transactions,
    )

    average_outgoing = safe_divide(
        outgoing_value,
        outgoing_transactions,
    )

    incoming_outgoing_ratio = safe_divide(
        incoming_value,
        outgoing_value,
    )

    outgoing_concentration = _get_numeric(
        graph,
        "outgoing_concentration",
    )

    incoming_concentration = _get_numeric(
        graph,
        "incoming_concentration",
    )

    # ------------------------------------------------------------
    # Maximum transaction values
    # ------------------------------------------------------------
    #
    # The timeline contains the actual transaction records.
    # Calculate maximum incoming/outgoing transaction values
    # directly from those records instead of relying on fields
    # that the timeline service does not currently provide.
    #

    timeline_transactions = timeline.get(
        "transactions",
        [],
    )

    outgoing_values: list[float] = []
    incoming_values: list[float] = []

    for transaction in timeline_transactions:
        if not isinstance(
            transaction,
            dict,
        ):
            continue

        value = _get_numeric(
            transaction,
            "value",
        )

        direction = str(
            transaction.get(
                "direction",
                "",
            )
        ).lower().strip()

        if direction == "outgoing":
            outgoing_values.append(value)

        elif direction == "incoming":
            incoming_values.append(value)

    maximum_outgoing_value = (
        max(outgoing_values)
        if outgoing_values
        else 0.0
    )

    maximum_incoming_value = (
        max(incoming_values)
        if incoming_values
        else 0.0
    )

    # ------------------------------------------------------------
    # Counterparty / network
    # ------------------------------------------------------------

    total_unique_counterparties = (
        unique_incoming
        + unique_outgoing
    )

    fan_in = _get_numeric(
        graph,
        "fan_in",
        unique_incoming,
    )

    fan_out = _get_numeric(
        graph,
        "fan_out",
        unique_outgoing,
    )

    multi_hop_exposure = _get_numeric(
        graph,
        "multi_hop_exposure_count",
    )

    # Existing graph analytics may expose
    # top counterparties with transaction counts.
    #
    # Count counterparties that appear more than once.

    counterparty_reuse_count = 0.0

    for key in (
        "top_outgoing_counterparties",
        "top_incoming_counterparties",
    ):
        counterparties = graph.get(
            key,
            [],
        )

        for counterparty in counterparties:
            if not isinstance(
                counterparty,
                dict,
            ):
                continue

            transaction_count_value = _get_numeric(
                counterparty,
                "transaction_count",
            )

            if transaction_count_value > 1:
                counterparty_reuse_count += 1

    # ------------------------------------------------------------
    # Fee behavior
    # ------------------------------------------------------------
    #
    # Current Neo4j transaction records do not yet expose
    # complete transaction receipt fee fields.
    #
    # Therefore we keep these as zero rather than inventing
    # values. The production EVM ingestion layer will later
    # populate them from transaction receipts.

    total_transaction_fees = 0.0
    average_transaction_fee = 0.0
    minimum_transaction_fee = 0.0
    maximum_transaction_fee = 0.0

    fee_to_value_ratio = 0.0

    # ------------------------------------------------------------
    # Temporal behavior
    # ------------------------------------------------------------

    average_gap = _get_numeric(
        timeline,
        "average_transaction_gap_seconds",
    )

    minimum_gap = _get_numeric(
        timeline,
        "shortest_transaction_gap_seconds",
    )

    maximum_gap = _get_numeric(
        timeline,
        "longest_transaction_gap_seconds",
    )

    bursts = timeline.get(
        "bursts",
        [],
    )

    transaction_burst_count = float(
        len(bursts)
    )

    temporal_signals = timeline.get(
        "temporal_signals",
        [],
    )

    rapid_sequence_count = 0

    for signal in temporal_signals:

        if not isinstance(
            signal,
            dict,
        ):
            continue

        signal_name = str(
            signal.get(
                "signal",
                "",
            )
        ).lower()

        if (
            "rapid" in signal_name
            or "sequence" in signal_name
        ):
            rapid_sequence_count += 1

    # ------------------------------------------------------------
    # Standardized output
    # ------------------------------------------------------------

    return {
        "transaction_count": transaction_count,

        "incoming_transaction_count": (
            incoming_transactions
        ),

        "outgoing_transaction_count": (
            outgoing_transactions
        ),

        "unique_incoming_counterparties": (
            unique_incoming
        ),

        "unique_outgoing_counterparties": (
            unique_outgoing
        ),

        "activity_duration_seconds": (
            activity_duration
        ),

        "total_incoming_value": (
            incoming_value
        ),

        "total_outgoing_value": (
            outgoing_value
        ),

        "average_incoming_value": (
            average_incoming
        ),

        "average_outgoing_value": (
            average_outgoing
        ),

        "maximum_incoming_value": (
            maximum_incoming_value
        ),

        "maximum_outgoing_value": (
            maximum_outgoing_value
        ),

        "incoming_outgoing_value_ratio": (
            incoming_outgoing_ratio
        ),

        "outgoing_value_concentration": (
            outgoing_concentration
        ),

        "incoming_value_concentration": (
            incoming_concentration
        ),

        "total_unique_counterparties": (
            total_unique_counterparties
        ),

        "counterparty_reuse_count": (
            counterparty_reuse_count
        ),

        "fan_in": fan_in,

        "fan_out": fan_out,

        "graph_multi_hop_exposure_count": (
            multi_hop_exposure
        ),

        "total_transaction_fees": (
            total_transaction_fees
        ),

        "average_transaction_fee": (
            average_transaction_fee
        ),

        "minimum_transaction_fee": (
            minimum_transaction_fee
        ),

        "maximum_transaction_fee": (
            maximum_transaction_fee
        ),

        "fee_to_value_ratio": (
            fee_to_value_ratio
        ),

        "average_transaction_gap_seconds": (
            average_gap
        ),

        "minimum_transaction_gap_seconds": (
            minimum_gap
        ),

        "maximum_transaction_gap_seconds": (
            maximum_gap
        ),

        "transaction_burst_count": (
            transaction_burst_count
        ),

        "rapid_transaction_sequence_count": (
            float(rapid_sequence_count)
        ),
    }