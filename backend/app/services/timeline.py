from datetime import datetime, timezone

from app.db.neo4j import get_wallet_timeline


def _parse_timestamp(timestamp: str | None):
    if not timestamp:
        return None

    try:
        value = timestamp.strip()

        if value.endswith("Z"):
            value = value[:-1] + "+00:00"

        parsed = datetime.fromisoformat(value)

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed

    except (ValueError, TypeError):
        return None


def _normalize_transaction(transaction: dict) -> dict:
    """
    Normalize a Neo4j transaction record so it matches the
    TimelineTransactionResponse schema.

    Neo4j/live blockchain data can contain a missing or null
    transaction value. The timeline analytics already treats
    missing values as zero, so normalize the returned record
    consistently before FastAPI/Pydantic validates the response.
    """
    normalized = dict(transaction)

    raw_value = normalized.get("value")

    try:
        normalized["value"] = float(raw_value or 0)
    except (TypeError, ValueError):
        normalized["value"] = 0.0

    return normalized


def _sort_transactions(transactions: list[dict]):
    return sorted(
        transactions,
        key=lambda transaction: (
            _parse_timestamp(transaction.get("timestamp"))
            or datetime.min.replace(tzinfo=timezone.utc)
        ),
    )


def _calculate_transaction_gaps(transactions: list[dict]):
    timestamps = []

    for transaction in transactions:
        parsed = _parse_timestamp(transaction.get("timestamp"))

        if parsed is not None:
            timestamps.append(parsed)

    timestamps.sort()

    gaps = []

    for previous, current in zip(timestamps, timestamps[1:]):
        gap = (current - previous).total_seconds()

        if gap >= 0:
            gaps.append(gap)

    return gaps


def _calculate_bursts(
    transactions: list[dict],
    burst_window_seconds: int = 3600,
    minimum_transactions: int = 3,
):
    timestamped_transactions = []

    for transaction in transactions:
        parsed = _parse_timestamp(transaction.get("timestamp"))

        if parsed is not None:
            timestamped_transactions.append(
                (parsed, transaction)
            )

    timestamped_transactions.sort(key=lambda item: item[0])

    bursts = []
    start_index = 0

    for end_index in range(len(timestamped_transactions)):
        while (
            timestamped_transactions[end_index][0]
            - timestamped_transactions[start_index][0]
        ).total_seconds() > burst_window_seconds:
            start_index += 1

        transaction_count = end_index - start_index + 1

        if transaction_count >= minimum_transactions:
            start_time = timestamped_transactions[start_index][0]
            end_time = timestamped_transactions[end_index][0]

            bursts.append(
                {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "transaction_count": transaction_count,
                    "duration_seconds": (
                        end_time - start_time
                    ).total_seconds(),
                }
            )

    # Remove overlapping duplicate bursts.
    unique_bursts = []

    for burst in bursts:
        if not unique_bursts:
            unique_bursts.append(burst)
            continue

        previous = unique_bursts[-1]

        if (
            burst["start_time"] == previous["start_time"]
            and burst["end_time"] == previous["end_time"]
        ):
            continue

        if (
            burst["start_time"] == previous["start_time"]
            and burst["transaction_count"]
            <= previous["transaction_count"]
        ):
            continue

        unique_bursts.append(burst)

    return unique_bursts


def _build_temporal_signals(
    transactions: list[dict],
    gaps: list[float],
    bursts: list[dict],
):
    signals = []

    if len(transactions) >= 5:
        signals.append(
            {
                "signal": "high_temporal_activity",
                "severity": "medium",
                "reason": (
                    f"{len(transactions)} transactions were observed "
                    "in the analyzed timeline."
                ),
                "evidence": {
                    "transaction_count": len(transactions),
                    "threshold": 5,
                },
            }
        )

    short_gaps = [
        gap
        for gap in gaps
        if gap <= 300
    ]

    if len(short_gaps) >= 2:
        signals.append(
            {
                "signal": "rapid_transaction_sequence",
                "severity": "medium",
                "reason": (
                    "Multiple transactions occurred within "
                    "five minutes of the previous transaction."
                ),
                "evidence": {
                    "short_gap_count": len(short_gaps),
                    "threshold_seconds": 300,
                },
            }
        )

    if bursts:
        largest_burst = max(
            bursts,
            key=lambda burst: burst["transaction_count"],
        )

        signals.append(
            {
                "signal": "transaction_burst",
                "severity": "medium",
                "reason": (
                    "Multiple transactions were concentrated "
                    "within a short time window."
                ),
                "evidence": {
                    "burst_count": len(bursts),
                    "largest_burst_transaction_count": (
                        largest_burst["transaction_count"]
                    ),
                    "largest_burst_start": (
                        largest_burst["start_time"]
                    ),
                    "largest_burst_end": (
                        largest_burst["end_time"]
                    ),
                },
            }
        )

    return signals


def analyze_wallet_timeline(
    address: str,
    chain: str,
):
    result = get_wallet_timeline(address, chain)

    if result is None:
        return None

    outgoing_transactions = [
        _normalize_transaction(transaction)
        for transaction in result["outgoing_transactions"]
    ]

    incoming_transactions = [
        _normalize_transaction(transaction)
        for transaction in result["incoming_transactions"]
    ]

    transactions = (
        outgoing_transactions
        + incoming_transactions
    )

    transactions = _sort_transactions(transactions)

    incoming_value = sum(
        float(transaction.get("value") or 0)
        for transaction in incoming_transactions
    )

    outgoing_value = sum(
        float(transaction.get("value") or 0)
        for transaction in outgoing_transactions
    )

    total_value = incoming_value + outgoing_value

    timestamped_transactions = [
        transaction
        for transaction in transactions
        if _parse_timestamp(transaction.get("timestamp")) is not None
    ]

    if timestamped_transactions:
        first_activity = timestamped_transactions[0]["timestamp"]
        last_activity = timestamped_transactions[-1]["timestamp"]

        first_datetime = _parse_timestamp(first_activity)
        last_datetime = _parse_timestamp(last_activity)

        activity_duration_seconds = (
            last_datetime - first_datetime
        ).total_seconds()
    else:
        first_activity = None
        last_activity = None
        activity_duration_seconds = 0.0

    gaps = _calculate_transaction_gaps(transactions)

    average_gap = (
        sum(gaps) / len(gaps)
        if gaps
        else None
    )

    shortest_gap = min(gaps) if gaps else None
    longest_gap = max(gaps) if gaps else None

    bursts = _calculate_bursts(transactions)

    largest_transactions = sorted(
        transactions,
        key=lambda transaction: float(
            transaction.get("value") or 0
        ),
        reverse=True,
    )[:10]

    temporal_signals = _build_temporal_signals(
        transactions,
        gaps,
        bursts,
    )

    return {
        "address": result["address"],
        "chain": result["chain"],
        "first_activity": first_activity,
        "last_activity": last_activity,
        "total_transactions": len(transactions),
        "incoming_transactions": len(incoming_transactions),
        "outgoing_transactions": len(outgoing_transactions),
        "incoming_value": incoming_value,
        "outgoing_value": outgoing_value,
        "total_value": total_value,
        "activity_duration_seconds": activity_duration_seconds,
        "average_transaction_gap_seconds": average_gap,
        "shortest_transaction_gap_seconds": shortest_gap,
        "longest_transaction_gap_seconds": longest_gap,
        "bursts": bursts,
        "largest_transactions": largest_transactions,
        "transactions": transactions,
        "temporal_signals": temporal_signals,
    }