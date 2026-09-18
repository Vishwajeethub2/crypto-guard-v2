from collections import defaultdict
from typing import Any

from app.db.neo4j import (
    analyze_wallet_graph,
    get_multi_hop_risk_paths,
)


def _calculate_counterparties(
    transfers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    counterparties: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "transaction_count": 0,
            "total_value": 0.0,
        }
    )

    for transfer in transfers:
        address = transfer.get("address")

        if not address:
            continue

        address = address.lower()
        value = float(transfer.get("value") or 0)

        counterparties[address]["transaction_count"] += 1
        counterparties[address]["total_value"] += value

    results = []

    for address, data in counterparties.items():
        results.append(
            {
                "address": address,
                "transaction_count": data["transaction_count"],
                "total_value": round(data["total_value"], 8),
            }
        )

    results.sort(
        key=lambda item: item["total_value"],
        reverse=True,
    )

    return results


def _calculate_concentration(
    transfers: list[dict[str, Any]],
) -> float:
    if not transfers:
        return 0.0

    total_value = sum(
        float(transfer.get("value") or 0)
        for transfer in transfers
    )

    if total_value <= 0:
        return 0.0

    counterparties = _calculate_counterparties(transfers)

    if not counterparties:
        return 0.0

    largest_value = counterparties[0]["total_value"]

    return round(
        largest_value / total_value,
        4,
    )


def _build_graph_signals(
    *,
    fan_out: int,
    fan_in: int,
    outgoing_transaction_count: int,
    incoming_transaction_count: int,
    outgoing_concentration: float,
    incoming_concentration: float,
    multi_hop_exposure_count: int,
) -> list[dict[str, Any]]:
    signals = []

    if fan_out >= 3:
        signals.append(
            {
                "signal": "high_fan_out",
                "severity": "medium",
                "reason": (
                    f"Wallet sends to {fan_out} unique counterparties."
                ),
                "evidence": {
                    "fan_out": fan_out,
                    "threshold": 3,
                },
            }
        )

    if fan_in >= 3:
        signals.append(
            {
                "signal": "high_fan_in",
                "severity": "medium",
                "reason": (
                    f"Wallet receives from {fan_in} unique counterparties."
                ),
                "evidence": {
                    "fan_in": fan_in,
                    "threshold": 3,
                },
            }
        )

    if outgoing_transaction_count >= 5 and fan_out >= 3:
        signals.append(
            {
                "signal": "distributed_outgoing_activity",
                "severity": "medium",
                "reason": (
                    "Wallet has multiple outgoing transactions "
                    "distributed across several counterparties."
                ),
                "evidence": {
                    "outgoing_transaction_count": (
                        outgoing_transaction_count
                    ),
                    "fan_out": fan_out,
                },
            }
        )

    if incoming_transaction_count >= 5 and fan_in >= 3:
        signals.append(
            {
                "signal": "distributed_incoming_activity",
                "severity": "medium",
                "reason": (
                    "Wallet has multiple incoming transactions "
                    "distributed across several counterparties."
                ),
                "evidence": {
                    "incoming_transaction_count": (
                        incoming_transaction_count
                    ),
                    "fan_in": fan_in,
                },
            }
        )

    if outgoing_concentration >= 0.75:
        signals.append(
            {
                "signal": "high_outgoing_concentration",
                "severity": "medium",
                "reason": (
                    "A large proportion of outgoing value "
                    "is concentrated with one counterparty."
                ),
                "evidence": {
                    "outgoing_concentration": outgoing_concentration,
                    "threshold": 0.75,
                },
            }
        )

    if incoming_concentration >= 0.75:
        signals.append(
            {
                "signal": "high_incoming_concentration",
                "severity": "medium",
                "reason": (
                    "A large proportion of incoming value "
                    "is concentrated with one counterparty."
                ),
                "evidence": {
                    "incoming_concentration": incoming_concentration,
                    "threshold": 0.75,
                },
            }
        )

    if multi_hop_exposure_count > 0:
        signals.append(
            {
                "signal": "multi_hop_risk_exposure",
                "severity": "high",
                "reason": (
                    f"Wallet has {multi_hop_exposure_count} "
                    "graph path(s) leading to risk intelligence."
                ),
                "evidence": {
                    "multi_hop_exposure_count": (
                        multi_hop_exposure_count
                    ),
                },
            }
        )

    return signals


def analyze_wallet_graph_analytics(
    address: str,
    chain: str,
    max_hops: int = 2,
):
    chain = chain.lower()

    graph_data = analyze_wallet_graph(
        address=address,
        chain=chain,
        max_hops=max_hops,
    )

    if graph_data is None:
        return None

    outgoing_transfers = graph_data["outgoing_transfers"]
    incoming_transfers = graph_data["incoming_transfers"]

    outgoing_counterparties = _calculate_counterparties(
        outgoing_transfers
    )

    incoming_counterparties = _calculate_counterparties(
        incoming_transfers
    )

    outgoing_concentration = _calculate_concentration(
        outgoing_transfers
    )

    incoming_concentration = _calculate_concentration(
        incoming_transfers
    )

    multi_hop_paths = get_multi_hop_risk_paths(
        address=address,
        chain=chain,
        max_hops=max_hops,
    )

    graph_signals = _build_graph_signals(
        fan_out=len(outgoing_counterparties),
        fan_in=len(incoming_counterparties),
        outgoing_transaction_count=len(outgoing_transfers),
        incoming_transaction_count=len(incoming_transfers),
        outgoing_concentration=outgoing_concentration,
        incoming_concentration=incoming_concentration,
        multi_hop_exposure_count=len(multi_hop_paths),
    )

    return {
        "address": graph_data["address"],
        "chain": graph_data["chain"],
        "outgoing_connections": len(outgoing_counterparties),
        "incoming_connections": len(incoming_counterparties),
        "outgoing_transaction_count": len(outgoing_transfers),
        "incoming_transaction_count": len(incoming_transfers),
        "outgoing_value": round(
            sum(
                float(item.get("value") or 0)
                for item in outgoing_transfers
            ),
            8,
        ),
        "incoming_value": round(
            sum(
                float(item.get("value") or 0)
                for item in incoming_transfers
            ),
            8,
        ),
        "fan_out": len(outgoing_counterparties),
        "fan_in": len(incoming_counterparties),
        "top_outgoing_counterparties": outgoing_counterparties[:10],
        "top_incoming_counterparties": incoming_counterparties[:10],
        "outgoing_concentration": outgoing_concentration,
        "incoming_concentration": incoming_concentration,
        "multi_hop_risk_paths": multi_hop_paths,
        "multi_hop_exposure_count": len(multi_hop_paths),
        "graph_signals": graph_signals,
    }
    