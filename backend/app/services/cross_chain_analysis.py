from app.db.neo4j import get_cross_chain_transfer_candidates


def _safe_float(value):
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _asset_changed(source_asset, destination_asset):
    if source_asset is None or destination_asset is None:
        return None

    return str(source_asset).strip().lower() != str(destination_asset).strip().lower()


def _build_candidate(record):
    source = {
        "address": record.get("source_address"),
        "receiver_address": record.get("source_receiver_address"),
        "chain": record.get("source_chain"),
        "transaction_hash": record.get("source_transaction_hash"),
        "asset": record.get("source_asset"),
        "value": _safe_float(record.get("source_value")),
        "category": record.get("source_category"),
        "block_number": record.get("source_block_number"),
        "timestamp": record.get("source_timestamp"),
        "contract_address": record.get("source_contract_address"),
    }

    destination = {
        "sender_address": record.get("destination_sender_address"),
        "address": record.get("destination_address"),
        "chain": record.get("destination_chain"),
        "transaction_hash": record.get("destination_transaction_hash"),
        "asset": record.get("destination_asset"),
        "value": _safe_float(record.get("destination_value")),
        "category": record.get("destination_category"),
        "block_number": record.get("destination_block_number"),
        "timestamp": record.get("destination_timestamp"),
        "contract_address": record.get("destination_contract_address"),
    }

    time_gap_seconds = _safe_float(record.get("time_gap_seconds"))
    value_difference = _safe_float(record.get("value_difference"))

    source_value = source["value"]
    destination_value = destination["value"]

    value_ratio = None

    if source_value is not None and source_value != 0 and destination_value is not None:
        value_ratio = destination_value / source_value

    asset_changed = _asset_changed(
        source["asset"],
        destination["asset"],
    )

    signals = []

    if time_gap_seconds is not None:
        signals.append("Temporal proximity")

    if source_value is not None and destination_value is not None:
        signals.append("Value proximity")

    if asset_changed is True:
        signals.append("Asset transformation")
    elif asset_changed is False:
        signals.append("Same asset")

    if (
        source["chain"]
        and destination["chain"]
        and source["chain"].lower() != destination["chain"].lower()
    ):
        signals.append("Different blockchain")

    signal_count = len(signals)

    confidence = min(
        0.95,
        0.25 + (signal_count * 0.15),
    )

    evidence = []

    if time_gap_seconds is not None:
        evidence.append(
            f"Transfers occur within {time_gap_seconds:.0f} seconds"
        )

    if value_difference is not None:
        evidence.append(
            f"Absolute transfer value difference: {value_difference:.6f}"
        )

    if source_value is not None and destination_value is not None:
        if value_ratio is not None:
            evidence.append(
                f"Destination/source value ratio: {value_ratio:.6f}"
            )

    if asset_changed is True:
        evidence.append(
            "Source and destination assets are different"
        )
    elif asset_changed is False:
        evidence.append(
            "Source and destination assets match"
        )

    if source["chain"] and destination["chain"]:
        evidence.append(
            f"Cross-chain movement: "
            f"{source['chain']} -> {destination['chain']}"
        )

    return {
        "source": source,
        "destination": destination,
        "time_gap_seconds": time_gap_seconds,
        "value_difference": value_difference,
        "value_ratio": value_ratio,
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
):
    """
    Analyze possible cross-chain transfer relationships.

    This function reads existing Neo4j transaction data only.
    It does not perform live blockchain ingestion or call Alchemy.

    Results are research candidates based on matching signals.
    They are not confirmed bridge-attribution results.
    """

    if not address:
        raise ValueError("Wallet address is required")

    address = address.lower().strip()
    source_chain = source_chain.lower().strip()

    if target_chain:
        target_chain = target_chain.lower().strip()

    if time_window_minutes < 1 or time_window_minutes > 1440:
        raise ValueError(
            "time_window_minutes must be between 1 and 1440"
        )

    if value_tolerance < 0 or value_tolerance > 1:
        raise ValueError(
            "value_tolerance must be between 0 and 1"
        )

    records = get_cross_chain_transfer_candidates(
        address=address,
        source_chain=source_chain,
        target_chain=target_chain,
        time_window_minutes=time_window_minutes,
        value_tolerance=value_tolerance,
        limit=250,
    )

    candidates = [
        _build_candidate(record)
        for record in records
    ]

    candidates.sort(
        key=lambda candidate: (
            -candidate["signal_count"],
            candidate["time_gap_seconds"]
            if candidate["time_gap_seconds"] is not None
            else float("inf"),
        )
    )

    return {
        "address": address,
        "source_chain": source_chain,
        "target_chain": target_chain,
        "time_window_minutes": time_window_minutes,
        "value_tolerance": value_tolerance,
        "status": (
            "candidates_found"
            if candidates
            else "no_candidates"
        ),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "notice": (
            "Cross-chain links are research candidates based "
            "on matching signals, not confirmed bridge attribution."
        ),
    }