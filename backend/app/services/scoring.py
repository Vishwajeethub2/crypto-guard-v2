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


def calculate_risk_score(
    indicators: list[dict],
    exposures: list[dict] | None = None,
):
    score = 0

    for indicator in indicators:
        severity = indicator.get("severity", "low").lower()
        score += SEVERITY_POINTS.get(severity, 0)

    for exposure in exposures or []:
        entity_type = exposure.get("entity_type", "").lower()
        score += EXPOSURE_POINTS.get(entity_type, 10)

    return min(score, 100)


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

    indicators = indicator_analysis["indicators"]
    exposures = exposure_analysis["exposures"]

    score = calculate_risk_score(
        indicators,
        exposures,
    )

    level = get_risk_level(score)

    return {
        "address": indicator_analysis["address"],
        "chain": indicator_analysis["chain"],
        "risk_score": score,
        "risk_level": level,
        "indicator_count": len(indicators),
        "exposure_count": len(exposures),
        "severity_counts": indicator_analysis["severity_counts"],
        "behavior": indicator_analysis["behavior"],
        "indicators": indicators,
        "exposures": exposures,
    }