from datetime import datetime, timezone

from app.services.exposure import analyze_risk_exposure
from app.services.risk import analyze_wallet_risk_indicators


SEVERITY_POINTS = {
    "low": 5,
    "medium": 15,
    "high": 25,
    "critical": 40,
}


EXPOSURE_POINTS = {
    "test_flag": 10,
    "sanctions": 40,
    "known_illicit": 35,
    "mixer": 20,
    "high_risk_service": 20,
}


RISK_CATEGORY_POINTS = {
    "fraud": 5,
    "scam": 5,
    "theft": 5,
    "ransomware": 10,
    "darknet": 10,
    "sanctions_evasion": 10,
    "money_laundering": 10,
}


SOURCE_RELIABILITY = {
    "internal_test_data": 0.50,
    "community_report": 0.70,
    "public_database": 0.85,
    "trusted_provider": 1.00,
}


def get_source_reliability(source: str | None):
    if not source:
        return 1.0

    source = source.lower().strip()

    return SOURCE_RELIABILITY.get(
        source,
        1.0,
    )


def get_intelligence_freshness(
    updated_at: str | None,
):
    if not updated_at:
        return 1.0

    try:
        timestamp = updated_at.strip()

        if timestamp.endswith("Z"):
            timestamp = timestamp[:-1] + "+00:00"

        updated_datetime = datetime.fromisoformat(
            timestamp
        )

        if updated_datetime.tzinfo is None:
            updated_datetime = updated_datetime.replace(
                tzinfo=timezone.utc
            )

        now = datetime.now(timezone.utc)

        age_days = (
            now - updated_datetime
        ).total_seconds() / 86400

        if age_days < 0:
            age_days = 0

        if age_days <= 30:
            return 1.00

        if age_days <= 90:
            return 0.85

        if age_days <= 180:
            return 0.70

        if age_days <= 365:
            return 0.50

        return 0.25

    except (ValueError, TypeError):
        return 1.0


def calculate_risk_score(
    indicators: list[dict],
    exposures: list[dict] | None = None,
):
    score = 0.0

    for indicator in indicators:
        severity = indicator.get(
            "severity",
            "low",
        ).lower()

        score += SEVERITY_POINTS.get(
            severity,
            0,
        )

    for exposure in exposures or []:
        entity_type = exposure.get(
            "entity_type",
            "",
        ).lower()

        base_points = EXPOSURE_POINTS.get(
            entity_type,
            10,
        )

        confidence = exposure.get(
            "confidence",
        )

        if confidence is None:
            confidence = 1.0

        confidence = float(confidence)
        confidence = max(
            0.0,
            min(confidence, 1.0),
        )

        source = exposure.get(
            "source",
        )

        source_reliability = get_source_reliability(
            source
        )

        freshness = get_intelligence_freshness(
            exposure.get("updated_at")
        )

        effective_confidence = (
            confidence
            * source_reliability
            * freshness
        )

        score += (
            base_points
            * effective_confidence
        )

        risk_category = exposure.get(
            "risk_category",
        )

        if risk_category:
            risk_category = (
                risk_category
                .lower()
                .strip()
            )

            category_points = RISK_CATEGORY_POINTS.get(
                risk_category,
                0,
            )

            score += (
                category_points
                * effective_confidence
            )

    return min(
        int(round(score)),
        100,
    )


def get_risk_level(score: int):
    if score <= 24:
        return "low"

    if score <= 49:
        return "moderate"

    if score <= 74:
        return "high"

    return "critical"


def calculate_wallet_risk(
    address: str,
    chain: str,
    max_hops: int = 2,
):
    indicator_analysis = analyze_wallet_risk_indicators(
        address,
        chain,
    )

    exposure_analysis = analyze_risk_exposure(
        address,
        chain,
        max_hops,
    )

    indicators = indicator_analysis[
        "indicators"
    ]

    exposures = exposure_analysis[
        "exposures"
    ]

    score = calculate_risk_score(
        indicators,
        exposures,
    )

    level = get_risk_level(
        score,
    )

    return {
        "address": indicator_analysis[
            "address"
        ],
        "chain": indicator_analysis[
            "chain"
        ],
        "risk_score": score,
        "risk_level": level,
        "indicator_count": len(
            indicators
        ),
        "exposure_count": len(
            exposures
        ),
        "severity_counts": indicator_analysis[
            "severity_counts"
        ],
        "behavior": indicator_analysis[
            "behavior"
        ],
        "indicators": indicators,
        "exposures": exposures,
    }