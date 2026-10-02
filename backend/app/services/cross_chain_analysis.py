from __future__ import annotations

from typing import Any

from app.db.neo4j import (
    get_bitcoin_cross_chain_transfer_candidates,
    get_cross_chain_transfer_candidates,
)


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        number = float(value)
        return number if number == number else None
    except (TypeError, ValueError):
        return None


def _asset_changed(source_asset: Any, destination_asset: Any) -> bool | None:
    if not source_asset or not destination_asset:
        return None
    return str(source_asset).strip().lower() != str(destination_asset).strip().lower()


def _build_candidate(
    record: dict[str, Any],
    time_window_minutes: int,
    value_tolerance: float,
) -> dict[str, Any]:
    source_value = _safe_float(record.get("source_value"))
    destination_value = _safe_float(record.get("destination_value"))
    time_gap = _safe_float(record.get("time_gap_seconds"))
    value_difference = _safe_float(record.get("value_difference"))

    # Neo4j explicitly marks Bitcoin -> EVM values as non-comparable.
    # Existing EVM -> EVM records may omit this field, so None preserves
    # the previous behavior for those records.
    value_comparable = record.get("value_comparable")

    value_ratio = None

    if (
        value_comparable is not False
        and source_value is not None
        and source_value != 0
        and destination_value is not None
    ):
        value_ratio = destination_value / source_value

    signals: list[str] = []

    if time_gap is not None and time_gap <= time_window_minutes * 60:
        signals.append("Temporal proximity")

    if (
        value_comparable is not False
        and source_value is not None
        and destination_value is not None
    ):
        if source_value == 0:
            signals.append("Value data available")
        elif (
            value_difference is not None
            and value_difference <= abs(source_value) * value_tolerance
        ):
            signals.append("Value proximity")

    asset_changed = _asset_changed(
        record.get("source_asset"),
        record.get("destination_asset"),
    )

    if asset_changed is True:
        signals.append("Asset transformation")
    elif asset_changed is False:
        signals.append("Same asset")

    source_chain = str(record.get("source_chain") or "").lower()
    destination_chain = str(record.get("destination_chain") or "").lower()

    if source_chain and destination_chain and source_chain != destination_chain:
        signals.append("Different blockchain")

    # Research-stage signal count only; it is not a fraud/risk verdict.
    signal_count = len(signals)
    confidence = round(min(1.0, signal_count / 4.0), 2)

    evidence = [
        "Source and destination transfers come from persisted Neo4j data",
        f"Transfers occur within {time_window_minutes} minute(s) of each other",
    ]

    if value_comparable is False:
        evidence.append(
            "Source and destination asset values are not directly comparable"
        )
    elif source_value is not None and destination_value is not None:
        evidence.append(
            f"Value difference is within {value_tolerance * 100:.0f}% tolerance"
        )

    if asset_changed is True:
        evidence.append("Asset differs between the source and destination events")

    return {
        "source": {
            "address": record.get("source_address"),
            "chain": record.get("source_chain"),
            "receiver_address": record.get("source_receiver_address"),
            "transaction_hash": record.get("source_transaction_hash"),
            "asset": record.get("source_asset"),
            "value": source_value,
            "category": record.get("source_category"),
            "block_number": record.get("source_block_number"),
            "timestamp": record.get("source_timestamp"),
            "contract_address": record.get("source_contract_address"),
        },
        "destination": {
            "sender_address": record.get("destination_sender_address"),
            "address": record.get("destination_address"),
            "chain": record.get("destination_chain"),
            "transaction_hash": record.get("destination_transaction_hash"),
            "asset": record.get("destination_asset"),
            "value": destination_value,
            "category": record.get("destination_category"),
            "block_number": record.get("destination_block_number"),
            "timestamp": record.get("destination_timestamp"),
            "contract_address": record.get("destination_contract_address"),
        },
        "time_gap_seconds": time_gap,
        "value_difference": value_difference,
        "value_ratio": value_ratio,
        "value_comparable": value_comparable,
        "asset_changed": asset_changed,
        "signals": signals,
        "signal_count": signal_count,
        "confidence": confidence,
        "status": "research_candidate",
        "evidence": evidence,
    }


def analyze_cross_chain(
    address: str,
    source_chain: str = "ethereum",
    target_chain: str | None = None,
    time_window_minutes: int = 120,
    value_tolerance: float = 0.20,
) -> dict[str, Any]:
    if time_window_minutes < 1 or time_window_minutes > 1440:
        raise ValueError("time_window_minutes must be between 1 and 1440")

    if value_tolerance < 0 or value_tolerance > 1:
        raise ValueError("value_tolerance must be between 0 and 1")

    source_chain = source_chain.lower().strip()
    target_chain = target_chain.lower().strip() if target_chain else None
    address = address.strip()

    if source_chain == "bitcoin":
        records = get_bitcoin_cross_chain_transfer_candidates(
            address=address,
            target_chain=target_chain,
            time_window_minutes=time_window_minutes,
            value_tolerance=value_tolerance,
        )
    else:
        address = address.lower()

        records = get_cross_chain_transfer_candidates(
            address=address,
            source_chain=source_chain,
            target_chain=target_chain,
            time_window_minutes=time_window_minutes,
            value_tolerance=value_tolerance,
        )

    candidates = [
        _build_candidate(
            record,
            time_window_minutes,
            value_tolerance,
        )
        for record in records
    ]

    candidates.sort(
        key=lambda item: (
            -item["signal_count"],
            (
                item["time_gap_seconds"]
                if item["time_gap_seconds"] is not None
                else float("inf")
            ),
            (
                item["value_difference"]
                if item["value_difference"] is not None
                else float("inf")
            ),
        )
    )

    return {
        "address": address,
        "source_chain": source_chain,
        "target_chain": target_chain,
        "time_window_minutes": time_window_minutes,
        "value_tolerance": value_tolerance,
        "status": "candidates_found" if candidates else "no_candidates",
        "candidate_count": len(candidates),
        "candidates": candidates,
        "notice": (
            "Cross-chain links are research candidates based on matching "
            "signals, not confirmed bridge attribution."
        ),
    }