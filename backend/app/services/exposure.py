from app.db.neo4j import get_risk_entity_exposure


def analyze_risk_exposure(
    address: str,
    chain: str,
    max_hops: int = 2,
):
    exposures = get_risk_entity_exposure(
        address,
        chain,
        max_hops,
    )

    return {
        "address": address,
        "chain": chain.lower(),
        "exposure_count": len(exposures),
        "exposures": exposures,
    }