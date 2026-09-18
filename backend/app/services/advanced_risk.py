from app.services.exposure import analyze_risk_exposure
from app.services.graph_analytics import analyze_wallet_graph_analytics
from app.services.risk import analyze_wallet_risk_indicators
from app.services.timeline import analyze_wallet_timeline


FACTOR_MAX_POINTS = {
    "connectivity": 15,
    "transaction_activity": 15,
    "value_flow": 15,
    "asset_diversity": 5,
    "intelligence_exposure": 40,
    "graph_risk": 5,
    "temporal_risk": 5,
}


def calculate_connectivity_factor(behavior: dict):
    connections = (
        behavior["outgoing_connections"]
        + behavior["incoming_connections"]
    )

    if connections >= 5:
        points = 15
    elif connections >= 3:
        points = 10
    elif connections >= 1:
        points = 5
    else:
        points = 0

    return {
        "factor": "connectivity",
        "contribution": points,
        "reason": (
            f"Wallet has {connections} total observed connections."
        ),
        "evidence": {
            "outgoing_connections": behavior["outgoing_connections"],
            "incoming_connections": behavior["incoming_connections"],
            "total_connections": connections,
        },
    }


def calculate_transaction_activity_factor(behavior: dict):
    transactions = behavior["total_transaction_count"]

    if transactions >= 20:
        points = 15
    elif transactions >= 10:
        points = 10
    elif transactions >= 5:
        points = 5
    else:
        points = 0

    return {
        "factor": "transaction_activity",
        "contribution": points,
        "reason": (
            f"Wallet has {transactions} observed transactions."
        ),
        "evidence": {
            "total_transactions": transactions,
            "incoming_transactions": behavior[
                "incoming_transaction_count"
            ],
            "outgoing_transactions": behavior[
                "outgoing_transaction_count"
            ],
        },
    }


def calculate_value_flow_factor(behavior: dict):
    outgoing_value = float(behavior["outgoing_value"])
    incoming_value = float(behavior["incoming_value"])
    total_value = outgoing_value + incoming_value

    if total_value >= 1_000_000:
        points = 15
    elif total_value >= 100_000:
        points = 10
    elif total_value >= 10_000:
        points = 5
    else:
        points = 0

    return {
        "factor": "value_flow",
        "contribution": points,
        "reason": (
            f"Wallet has observed total value flow of "
            f"{total_value:.2f}."
        ),
        "evidence": {
            "incoming_value": incoming_value,
            "outgoing_value": outgoing_value,
            "total_value": total_value,
        },
    }


def calculate_asset_diversity_factor(behavior: dict):
    unique_assets = behavior["unique_assets"]

    if unique_assets >= 5:
        points = 5
    elif unique_assets >= 3:
        points = 3
    elif unique_assets >= 2:
        points = 1
    else:
        points = 0

    return {
        "factor": "asset_diversity",
        "contribution": points,
        "reason": (
            f"Wallet has activity involving "
            f"{unique_assets} different assets."
        ),
        "evidence": {
            "unique_assets": unique_assets,
        },
    }


def calculate_intelligence_exposure_factor(exposures: list[dict]):
    points = 0

    for exposure in exposures:
        entity_type = (
            exposure.get("entity_type", "")
            .lower()
            .strip()
        )

        confidence = exposure.get("confidence")

        if confidence is None:
            confidence = 1.0

        confidence = max(
            0.0,
            min(float(confidence), 1.0),
        )

        if entity_type == "sanctions":
            points += 20 * confidence

        elif entity_type == "known_illicit":
            points += 15 * confidence

        elif entity_type == "mixer":
            points += 10 * confidence

        elif entity_type == "high_risk_service":
            points += 8 * confidence

        elif entity_type == "test_flag":
            points += 2 * confidence

        else:
            points += 2 * confidence

    points = min(round(points), 40)

    return {
        "factor": "intelligence_exposure",
        "contribution": points,
        "reason": (
            f"Wallet has {len(exposures)} observed intelligence exposures."
        ),
        "evidence": {
            "exposure_count": len(exposures),
            "entity_types": [
                exposure.get("entity_type")
                for exposure in exposures
            ],
        },
    }


def calculate_graph_risk_factor(graph_analysis: dict | None):
    if not graph_analysis:
        return {
            "factor": "graph_risk",
            "contribution": 0,
            "reason": "Graph analytics were not available.",
            "evidence": {},
        }

    points = 0

    outgoing_concentration = float(
        graph_analysis.get("outgoing_concentration", 0.0)
    )

    incoming_concentration = float(
        graph_analysis.get("incoming_concentration", 0.0)
    )

    multi_hop_exposure_count = int(
        graph_analysis.get("multi_hop_exposure_count", 0)
    )

    if outgoing_concentration >= 0.75:
        points += 3

    if incoming_concentration >= 0.75:
        points += 1

    if multi_hop_exposure_count > 0:
        points += 3

    points = min(points, FACTOR_MAX_POINTS["graph_risk"])

    return {
        "factor": "graph_risk",
        "contribution": points,
        "reason": (
            "Graph structure indicates concentrated value flow "
            "or multi-hop risk exposure."
            if points > 0
            else "No elevated graph-risk pattern was detected."
        ),
        "evidence": {
            "outgoing_concentration": outgoing_concentration,
            "incoming_concentration": incoming_concentration,
            "multi_hop_exposure_count": multi_hop_exposure_count,
            "graph_signals": graph_analysis.get(
                "graph_signals",
                [],
            ),
        },
    }


def calculate_temporal_risk_factor(
    timeline_analysis: dict | None,
):
    if not timeline_analysis:
        return {
            "factor": "temporal_risk",
            "contribution": 0,
            "reason": "Timeline analytics were not available.",
            "evidence": {},
        }

    points = 0

    bursts = timeline_analysis.get("bursts", [])
    temporal_signals = timeline_analysis.get(
        "temporal_signals",
        [],
    )

    shortest_gap = timeline_analysis.get(
        "shortest_transaction_gap_seconds"
    )

    total_transactions = int(
        timeline_analysis.get(
            "total_transactions",
            0,
        )
    )

    # A burst provides evidence of concentrated activity.
    if bursts:
        points += 2

    # Multiple temporal signals provide additional evidence,
    # but we cap the factor so it cannot dominate the assessment.
    if len(temporal_signals) >= 2:
        points += 2
    elif len(temporal_signals) == 1:
        points += 1

    # Very short transaction spacing is an additional temporal signal.
    if (
        shortest_gap is not None
        and float(shortest_gap) <= 300
    ):
        points += 1

    points = min(
        points,
        FACTOR_MAX_POINTS["temporal_risk"],
    )

    if points > 0:
        reason = (
            "Timeline analysis detected concentrated or "
            "rapid transaction activity."
        )
    else:
        reason = (
            "No elevated temporal activity pattern was detected."
        )

    return {
        "factor": "temporal_risk",
        "contribution": points,
        "reason": reason,
        "evidence": {
            "total_transactions": total_transactions,
            "burst_count": len(bursts),
            "temporal_signal_count": len(
                temporal_signals
            ),
            "shortest_transaction_gap_seconds": shortest_gap,
            "temporal_signals": temporal_signals,
        },
    }


def calculate_advanced_risk(
    behavior: dict,
    exposures: list[dict],
    graph_analysis: dict | None = None,
    timeline_analysis: dict | None = None,
):
    factors = [
        calculate_connectivity_factor(behavior),
        calculate_transaction_activity_factor(behavior),
        calculate_value_flow_factor(behavior),
        calculate_asset_diversity_factor(behavior),
        calculate_intelligence_exposure_factor(exposures),
        calculate_graph_risk_factor(graph_analysis),
        calculate_temporal_risk_factor(timeline_analysis),
    ]

    score = sum(
        factor["contribution"]
        for factor in factors
    )

    score = min(score, 100)

    if score <= 24:
        risk_level = "low"
    elif score <= 49:
        risk_level = "moderate"
    elif score <= 74:
        risk_level = "high"
    else:
        risk_level = "critical"

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "factors": factors,
        "behavior": behavior,
        "exposures": exposures,
    }


def analyze_wallet_advanced_risk(
    address: str,
    chain: str,
    max_hops: int = 2,
):
    indicator_analysis = analyze_wallet_risk_indicators(
        address,
        chain,
    )

    if indicator_analysis["behavior"] is None:
        return {
            "address": address,
            "chain": chain.lower(),
            "risk_score": 0,
            "risk_level": "low",
            "factors": [],
            "behavior": None,
            "exposures": [],
        }

    behavior = indicator_analysis["behavior"]

    exposure_analysis = analyze_risk_exposure(
        address,
        chain,
        max_hops,
    )

    exposures = exposure_analysis["exposures"]

    graph_analysis = analyze_wallet_graph_analytics(
        address,
        chain,
        max_hops,
    )

    timeline_analysis = analyze_wallet_timeline(
        address,
        chain,
    )

    result = calculate_advanced_risk(
        behavior=behavior,
        exposures=exposures,
        graph_analysis=graph_analysis,
        timeline_analysis=timeline_analysis,
    )

    return {
        "address": address,
        "chain": chain.lower(),
        "risk_score": result["risk_score"],
        "risk_level": result["risk_level"],
        "factors": result["factors"],
        "behavior": result["behavior"],
        "exposures": result["exposures"],
    }