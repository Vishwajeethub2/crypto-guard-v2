from app.db.neo4j import analyze_wallet_behavior


# Development-only thresholds.
HIGH_CONNECTION_THRESHOLD = 3
HIGH_TRANSACTION_THRESHOLD = 5
MULTI_ASSET_THRESHOLD = 3
LARGE_OUTGOING_THRESHOLD = 100000
HIGH_OUTGOING_RATIO_THRESHOLD = 0.80


# Development-only intelligence severity mapping.
# These are prototype classifications, not legal or regulatory determinations.
INTELLIGENCE_SEVERITY = {
    "test_flag": "low",
    "high_risk_service": "medium",
    "mixer": "high",
    "known_illicit": "high",
    "sanctions": "critical",
}


def generate_risk_indicators(behavior: dict):
    indicators = []

    outgoing_connections = behavior["outgoing_connections"]
    incoming_connections = behavior["incoming_connections"]

    outgoing_transactions = behavior["outgoing_transaction_count"]
    incoming_transactions = behavior["incoming_transaction_count"]
    total_transactions = behavior["total_transaction_count"]

    outgoing_value = float(behavior["outgoing_value"])
    incoming_value = float(behavior["incoming_value"])

    unique_assets = behavior["unique_assets"]

    total_value = incoming_value + outgoing_value

    outgoing_ratio = (
        outgoing_value / total_value
        if total_value > 0
        else 0.0
    )

    # 1. High outgoing connectivity
    if outgoing_connections >= HIGH_CONNECTION_THRESHOLD:
        indicators.append(
            {
                "indicator": "high_outgoing_connectivity",
                "severity": "medium",
                "reason": (
                    f"Wallet has {outgoing_connections} outgoing "
                    "connections, exceeding the development threshold."
                ),
                "evidence": {
                    "outgoing_connections": outgoing_connections,
                    "threshold": HIGH_CONNECTION_THRESHOLD,
                },
            }
        )

    # 2. High transaction activity
    if total_transactions >= HIGH_TRANSACTION_THRESHOLD:
        indicators.append(
            {
                "indicator": "high_transaction_activity",
                "severity": "medium",
                "reason": (
                    f"Wallet has {total_transactions} observed transactions, "
                    "exceeding the development threshold."
                ),
                "evidence": {
                    "total_transactions": total_transactions,
                    "incoming_transactions": incoming_transactions,
                    "outgoing_transactions": outgoing_transactions,
                    "threshold": HIGH_TRANSACTION_THRESHOLD,
                },
            }
        )

    # 3. Large outgoing volume
    if outgoing_value >= LARGE_OUTGOING_THRESHOLD:
        indicators.append(
            {
                "indicator": "large_outgoing_volume",
                "severity": "medium",
                "reason": (
                    f"Wallet has observed outgoing value of "
                    f"{outgoing_value:.2f}, exceeding the development threshold."
                ),
                "evidence": {
                    "outgoing_value": outgoing_value,
                    "threshold": LARGE_OUTGOING_THRESHOLD,
                },
            }
        )

    # 4. Outgoing-dominant activity
    if total_value > 0 and outgoing_ratio >= HIGH_OUTGOING_RATIO_THRESHOLD:
        indicators.append(
            {
                "indicator": "outgoing_dominant_activity",
                "severity": "low",
                "reason": (
                    f"{outgoing_ratio * 100:.1f}% of the observed wallet value "
                    "is outgoing."
                ),
                "evidence": {
                    "outgoing_value": outgoing_value,
                    "incoming_value": incoming_value,
                    "outgoing_ratio": round(outgoing_ratio, 4),
                    "threshold": HIGH_OUTGOING_RATIO_THRESHOLD,
                },
            }
        )

    # 5. Multiple asset activity
    if unique_assets >= MULTI_ASSET_THRESHOLD:
        indicators.append(
            {
                "indicator": "multiple_asset_activity",
                "severity": "low",
                "reason": (
                    f"Wallet has activity involving {unique_assets} "
                    "different assets."
                ),
                "evidence": {
                    "unique_assets": unique_assets,
                    "threshold": MULTI_ASSET_THRESHOLD,
                },
            }
        )

    # 6. No observed incoming activity
    if incoming_transactions == 0:
        indicators.append(
            {
                "indicator": "no_observed_incoming_activity",
                "severity": "low",
                "reason": (
                    "No incoming transactions were observed in the "
                    "currently analyzed graph data."
                ),
                "evidence": {
                    "incoming_transactions": incoming_transactions,
                    "incoming_value": incoming_value,
                },
            }
        )

    # 7. No observed outgoing activity
    if outgoing_transactions == 0:
        indicators.append(
            {
                "indicator": "no_observed_outgoing_activity",
                "severity": "low",
                "reason": (
                    "No outgoing transactions were observed in the "
                    "currently analyzed graph data."
                ),
                "evidence": {
                    "outgoing_transactions": outgoing_transactions,
                    "outgoing_value": outgoing_value,
                },
            }
        )

    return indicators


def analyze_wallet_risk_indicators(address: str, chain: str):
    behavior = analyze_wallet_behavior(address, chain)

    if behavior is None:
        return {
            "address": address,
            "chain": chain.lower(),
            "behavior": None,
            "indicators": [],
            "indicator_count": 0,
            "severity_counts": {
                "low": 0,
                "medium": 0,
                "high": 0,
                "critical": 0,
            },
        }

    indicators = generate_risk_indicators(behavior)

    severity_counts = {
        "low": 0,
        "medium": 0,
        "high": 0,
        "critical": 0,
    }

    for indicator in indicators:
        severity = indicator["severity"]

        if severity in severity_counts:
            severity_counts[severity] += 1

    return {
        "address": behavior["address"],
        "chain": behavior["chain"],
        "behavior": behavior,
        "indicators": indicators,
        "indicator_count": len(indicators),
        "severity_counts": severity_counts,
    }