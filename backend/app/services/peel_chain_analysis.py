from typing import Any, Dict, List, Optional

from app.db.neo4j import get_peel_chain_candidates


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_timestamp(value: Any) -> Optional[float]:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()

    if not text:
        return None

    try:
        return float(text)
    except ValueError:
        pass

    try:
        from datetime import datetime

        normalized = text.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized).timestamp()

    except (TypeError, ValueError, OverflowError):
        return None


def _calculate_value_progression(
    transfers: List[Dict[str, Any]],
) -> Dict[str, Any]:
    values = [
        _to_float(transfer.get("value"))
        for transfer in transfers
    ]

    if any(value is None for value in values):
        return {
            "input_value": None,
            "output_value": None,
            "value_difference": None,
            "value_ratio": None,
            "values": values,
            "available": False,
            "value_reduction": False,
            "retained_amount": None,
            "retention_ratio": None,
            "forward_ratio": None,
        }

    if not values:
        return {
            "input_value": None,
            "output_value": None,
            "value_difference": None,
            "value_ratio": None,
            "values": [],
            "available": False,
            "value_reduction": False,
            "retained_amount": None,
            "retention_ratio": None,
            "forward_ratio": None,
        }

    input_value = values[0]
    output_value = values[-1]

    value_difference = output_value - input_value

    if input_value != 0:
        value_ratio = output_value / input_value
    else:
        value_ratio = None

    value_reduction = (
        input_value > 0
        and output_value >= 0
        and output_value < input_value
    )

    retained_amount = None
    retention_ratio = None
    forward_ratio = None

    if value_reduction:
        retained_amount = input_value - output_value
        retention_ratio = retained_amount / input_value
        forward_ratio = output_value / input_value

    return {
        "input_value": input_value,
        "output_value": output_value,
        "value_difference": value_difference,
        "value_ratio": value_ratio,
        "values": values,
        "available": True,
        "value_reduction": value_reduction,
        "retained_amount": retained_amount,
        "retention_ratio": retention_ratio,
        "forward_ratio": forward_ratio,
    }


def _calculate_hop_value_progression(
    transfers: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    progression = []

    for index in range(1, len(transfers)):
        previous_value = _to_float(
            transfers[index - 1].get("value")
        )

        current_value = _to_float(
            transfers[index].get("value")
        )

        if previous_value is None or current_value is None:
            continue

        difference = current_value - previous_value

        if previous_value > 0:
            forward_ratio = current_value / previous_value
            retention_ratio = max(
                0.0,
                (previous_value - current_value) / previous_value,
            )
        else:
            forward_ratio = None
            retention_ratio = None

        value_reduction = (
            previous_value > 0
            and current_value >= 0
            and current_value < previous_value
        )

        progression.append(
            {
                "from_transaction": transfers[index - 1].get(
                    "transaction_hash"
                ),
                "to_transaction": transfers[index].get(
                    "transaction_hash"
                ),
                "input_value": previous_value,
                "forwarded_value": current_value,
                "value_difference": difference,
                "value_reduction": value_reduction,
                "retained_amount": (
                    previous_value - current_value
                    if value_reduction
                    else 0.0
                ),
                "forward_ratio": forward_ratio,
                "retention_ratio": retention_ratio,
            }
        )

    return progression


def _calculate_timing(
    transfers: List[Dict[str, Any]],
) -> Dict[str, Any]:
    timestamps = [
        _to_timestamp(transfer.get("timestamp"))
        for transfer in transfers
    ]

    if any(timestamp is None for timestamp in timestamps):
        return {
            "timestamps_available": False,
            "timestamps": timestamps,
            "gaps_seconds": [],
            "average_gap_seconds": None,
            "minimum_gap_seconds": None,
            "maximum_gap_seconds": None,
            "chronological": None,
        }

    gaps = []

    for index in range(1, len(timestamps)):
        previous = timestamps[index - 1]
        current = timestamps[index]

        gaps.append(current - previous)

    chronological = all(
        gap >= 0
        for gap in gaps
    )

    valid_gaps = [
        gap
        for gap in gaps
        if gap >= 0
    ]

    if not valid_gaps:
        return {
            "timestamps_available": True,
            "timestamps": timestamps,
            "gaps_seconds": gaps,
            "average_gap_seconds": None,
            "minimum_gap_seconds": None,
            "maximum_gap_seconds": None,
            "chronological": chronological,
        }

    return {
        "timestamps_available": True,
        "timestamps": timestamps,
        "gaps_seconds": valid_gaps,
        "average_gap_seconds": sum(valid_gaps) / len(valid_gaps),
        "minimum_gap_seconds": min(valid_gaps),
        "maximum_gap_seconds": max(valid_gaps),
        "chronological": chronological,
    }


def _get_assets(
    transfers: List[Dict[str, Any]],
) -> List[str]:
    assets = []

    for transfer in transfers:
        asset = transfer.get("asset")

        if asset is None:
            continue

        asset_text = str(asset).strip().lower()

        if asset_text:
            assets.append(asset_text)

    return assets


def _same_asset(
    transfers: List[Dict[str, Any]],
) -> Optional[bool]:
    assets = _get_assets(transfers)

    if len(assets) != len(transfers):
        return None

    return len(set(assets)) == 1


def _has_valid_wallet_sequence(
    wallets: List[Dict[str, Any]],
) -> bool:
    if len(wallets) < 3:
        return False

    addresses = [
        wallet.get("address")
        for wallet in wallets
    ]

    if any(not address for address in addresses):
        return False

    normalized = [
        str(address).lower()
        for address in addresses
    ]

    return len(normalized) == len(set(normalized))


def _has_required_transfer_data(
    transfers: List[Dict[str, Any]],
) -> bool:
    if len(transfers) < 2:
        return False

    for transfer in transfers:
        if not transfer.get("transaction_hash"):
            return False

        if _to_float(transfer.get("value")) is None:
            return False

        if not transfer.get("from_address"):
            return False

        if not transfer.get("to_address"):
            return False

    return True


def _has_valid_transfer_sequence(
    transfers: List[Dict[str, Any]],
) -> bool:
    """Verify that every transfer is actually connected to the next transfer."""
    if len(transfers) < 2:
        return False

    for index in range(1, len(transfers)):
        previous_transfer = transfers[index - 1]
        current_transfer = transfers[index]

        previous_to = str(previous_transfer.get("to_address", "")).lower()
        current_from = str(current_transfer.get("from_address", "")).lower()

        if not previous_to or not current_from:
            return False

        if previous_to != current_from:
            return False

    return True


def _passes_peel_chain_validation(
    transfers: List[Dict[str, Any]],
    timing: Dict[str, Any],
    same_asset: Optional[bool],
    value_progression: Dict[str, Any],
    hop_value_progression: List[Dict[str, Any]],
) -> bool:
    if len(transfers) < 2:
        return False

    if not value_progression["available"]:
        return False

    if not timing["timestamps_available"]:
        return False

    if timing["chronological"] is not True:
        return False

    if same_asset is not True:
        return False

    if not _has_valid_transfer_sequence(transfers):
        return False

    if not hop_value_progression:
        return False

    for hop in hop_value_progression:
        input_value = _to_float(hop.get("input_value"))
        forwarded_value = _to_float(hop.get("forwarded_value"))

        if input_value is None or forwarded_value is None:
            return False

        if input_value < 0 or forwarded_value < 0:
            return False

        if forwarded_value > input_value:
            return False

    return True


def _build_evidence(
    transfers: List[Dict[str, Any]],
    value_progression: Dict[str, Any],
    hop_value_progression: List[Dict[str, Any]],
    timing: Dict[str, Any],
    same_asset: Optional[bool],
) -> List[str]:
    evidence = []

    if len(transfers) >= 2:
        evidence.append(
            "Sequential directional transfers across multiple hops"
        )

    if value_progression["available"]:
        evidence.append(
            "Numeric transfer values are available across the sequence"
        )

    if timing["timestamps_available"]:
        evidence.append(
            "Transfer timestamps are available"
        )

    if timing["chronological"] is True:
        evidence.append(
            "Transfer timestamps are chronologically ordered"
        )

    if same_asset is True:
        evidence.append(
            "All transfers use the same asset"
        )

    if value_progression["value_reduction"]:
        evidence.append(
            "The final forwarded value is lower than the initial value"
        )

    if any(
        hop["value_reduction"]
        for hop in hop_value_progression
    ):
        evidence.append(
            "At least one sequential hop shows value reduction"
        )

    if hop_value_progression and all(
        hop["forwarded_value"] <= hop["input_value"]
        for hop in hop_value_progression
    ):
        evidence.append(
            "Every sequential hop maintains or reduces value"
        )

    return evidence


def _analyze_candidate(
    candidate: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    wallets = candidate.get("wallets") or []
    transfers = candidate.get("transfers") or []

    if not _has_valid_wallet_sequence(wallets):
        return None

    if not _has_required_transfer_data(transfers):
        return None

    value_progression = _calculate_value_progression(
        transfers
    )

    hop_value_progression = _calculate_hop_value_progression(
        transfers
    )

    timing = _calculate_timing(
        transfers
    )

    same_asset = _same_asset(
        transfers
    )

    if not _passes_peel_chain_validation(
        transfers=transfers,
        timing=timing,
        same_asset=same_asset,
        value_progression=value_progression,
        hop_value_progression=hop_value_progression,
    ):
        return None

    evidence = _build_evidence(
        transfers=transfers,
        value_progression=value_progression,
        hop_value_progression=hop_value_progression,
        timing=timing,
        same_asset=same_asset,
    )

    return {
        "wallets": wallets,
        "hop_count": len(transfers),
        "wallet_count": len(wallets),
        "transfers": transfers,
        "value_progression": value_progression,
        "hop_value_progression": hop_value_progression,
        "timing": timing,
        "same_asset": same_asset,
        "evidence": evidence,
    }


def _deduplicate_candidates(
    candidates: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    unique = {}

    for candidate in candidates:
        wallet_key = tuple(
            str(wallet.get("address", "")).lower()
            for wallet in candidate.get("wallets", [])
        )

        transaction_key = tuple(
            str(transfer.get("transaction_hash", "")).lower()
            for transfer in candidate.get("transfers", [])
        )

        key = (
            wallet_key,
            transaction_key,
        )

        if key not in unique:
            unique[key] = candidate

    return list(unique.values())


def _merge_overlapping_candidates(
    candidates: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Remove shorter candidates that are prefixes of longer candidates.

    Example:

        A -> B -> C
        A -> B -> C -> D

    becomes:

        A -> B -> C -> D

    This prevents the same underlying chain from appearing multiple
    times when Neo4j returns paths of different lengths.
    """

    if not candidates:
        return []

    candidates = sorted(
        candidates,
        key=lambda candidate: len(
            candidate.get("transfers", [])
        ),
        reverse=True,
    )

    merged = []

    for candidate in candidates:
        candidate_transactions = tuple(
            str(
                transfer.get("transaction_hash", "")
            ).lower()
            for transfer in candidate.get("transfers", [])
        )

        candidate_wallets = tuple(
            str(
                wallet.get("address", "")
            ).lower()
            for wallet in candidate.get("wallets", [])
        )

        is_contained = False

        for existing in merged:
            existing_transactions = tuple(
                str(
                    transfer.get("transaction_hash", "")
                ).lower()
                for transfer in existing.get("transfers", [])
            )

            existing_wallets = tuple(
                str(
                    wallet.get("address", "")
                ).lower()
                for wallet in existing.get("wallets", [])
            )

            candidate_is_prefix = (
                len(candidate_transactions)
                <= len(existing_transactions)
                and existing_transactions[
                    :len(candidate_transactions)
                ]
                == candidate_transactions
                and existing_wallets[
                    :len(candidate_wallets)
                ]
                == candidate_wallets
            )

            if candidate_is_prefix:
                is_contained = True
                break

        if not is_contained:
            merged.append(candidate)

    return merged


def analyze_peel_chain(
    address: str,
    chain: str = "ethereum",
    max_hops: int = 5,
) -> Dict[str, Any]:
    """
    Analyze existing Neo4j graph data for Peel Chain candidates.

    No external blockchain API is called.
    """

    candidates = get_peel_chain_candidates(
        address=address,
        chain=chain,
        max_hops=max_hops,
    )

    analyzed_candidates = []

    for candidate in candidates:
        analyzed = _analyze_candidate(candidate)

        if analyzed is not None:
            analyzed_candidates.append(analyzed)

    analyzed_candidates = _deduplicate_candidates(
        analyzed_candidates
    )

    analyzed_candidates = _merge_overlapping_candidates(
        analyzed_candidates
    )

    analyzed_candidates.sort(
        key=lambda candidate: (
            candidate["hop_count"],
            candidate["wallet_count"],
        )
    )

    return {
        "address": address,
        "chain": chain.lower(),
        "max_hops": max_hops,
        "status": (
            "candidates_found"
            if analyzed_candidates
            else "no_candidates_found"
        ),
        "candidate_count": len(analyzed_candidates),
        "candidates": analyzed_candidates,
        "notice": (
            "Research-stage analytical candidates based on stored "
            "transaction graph evidence. This analysis does not "
            "establish illicit activity."
        ),
    }