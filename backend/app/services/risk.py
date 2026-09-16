from app.db.neo4j import analyze_wallet_behavior


# Development-only thresholds.
# These are not regulatory or legal thresholds.
HIGH_CONNECTION_THRESHOLD = 3
HIGH_TRANSACTION_THRESHOLD = 5
MULTI_ASSET_THRESHOLD = 3
LARGE_OUTGOING_THRESHOLD = 100000
HIGH_OUTGOING_RATIO_THRESHOLD = 0.80


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
                "indicator": "HIGH_OUTGOING_CONNECTIVITY",
                "severity": "medium",
                "reason": (
                    "Wallet interacts with a relatively high number "
                    "of distinct outgoing counterparties."
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
                "indicator": "HIGH_TRANSACTION_ACTIVITY",
                "severity": "medium",
                "reason": (
                    "Wallet has a relatively high number of observed "
                    "transfer relationships."
                ),
                "evidence": {
                    "total_transactions": total_transactions,
                    "threshold": HIGH_TRANSACTION_THRESHOLD,
                },
            }
        )

    # 3. Large outgoing volume
    if outgoing_value >= LARGE_OUTGOING_THRESHOLD:
        indicators.append(
            {
                "indicator": "LARGE_OUTGOING_VOLUME",
                "severity": "medium",
                "reason": (
                    "Observed outgoing transfer volume exceeds the "
                    "configured development threshold."
                ),
                "evidence": {
                    "outgoing_value": outgoing_value,
                    "threshold": LARGE_OUTGOING_THRESHOLD,
                },
            }
        )

    # 4. Strongly outgoing-oriented activity
    if (
        total_value > 0
        and outgoing_ratio >= HIGH_OUTGOING_RATIO_THRESHOLD
        and outgoing_transactions > 0
    ):
        indicators.append(
            {
                "indicator": "OUTGOING_DOMINANT_ACTIVITY",
                "severity": "low",
                "reason": (
                    "Observed transfer value is strongly concentrated "
                    "on outgoing activity."
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
                "indicator": "MULTIPLE_ASSET_ACTIVITY",
                "severity": "low",
                "reason": (
                    "Wallet has interacted with multiple distinct assets."
                ),
                "evidence": {
                    "unique_assets": unique_assets,
                    "threshold": MULTI_ASSET_THRESHOLD,
                },
            }
        )

    # 6. No incoming activity
    if incoming_transactions == 0 and outgoing_transactions > 0:
        indicators.append(
            {
                "indicator": "NO_OBSERVED_INCOMING_ACTIVITY",
                "severity": "low",
                "reason": (
                    "The current dataset contains outgoing transfers "
                    "but no observed incoming transfers."
                ),
                "evidence": {
                    "incoming_transactions": incoming_transactions,
                    "outgoing_transactions": outgoing_transactions,
                },
            }
        )

    # 7. No outgoing activity
    if outgoing_transactions == 0 and incoming_transactions > 0:
        indicators.append(
            {
                "indicator": "NO_OBSERVED_OUTGOING_ACTIVITY",
                "severity": "low",
                "reason": (
                    "The current dataset contains incoming transfers "
                    "but no observed outgoing transfers."
                ),
                "evidence": {
                    "incoming_transactions": incoming_transactions,
                    "outgoing_transactions": outgoing_transactions,
                },
            }
        )

    return indicators


def analyze_wallet_risk_indicators(
    address: str,
    chain: str,
):
    behavior = analyze_wallet_behavior(
        address,
        chain,
    )

    if behavior is None:
        return {
            "address": address,
            "chain": chain.lower(),
            "behavior": None,
            "indicators": [],
            "indicator_count": 0,
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