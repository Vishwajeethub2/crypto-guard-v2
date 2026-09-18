from app.db.neo4j import (
    create_risk_entity,
    list_risk_entities,
    get_risk_entity,
    update_risk_entity,
    delete_risk_entity,
)

SUPPORTED_CHAINS = {
    "ethereum",
    "polygon",
    "arbitrum",
    "optimism",
    "base",
}

SUPPORTED_ENTITY_TYPES = {
    "test_flag",
    "high_risk_service",
    "mixer",
    "known_illicit",
    "sanctions",
}


def add_risk_entity(
    address: str,
    chain: str,
    entity_type: str,
    name: str,
    source: str,
    risk_category: str | None = None,
    confidence: float | None = None,
    evidence: str | None = None,
    updated_at: str | None = None,
):
    chain = chain.lower()
    entity_type = entity_type.lower().strip()

    if chain not in SUPPORTED_CHAINS:
        raise ValueError(
            f"Unsupported chain: {chain}. "
            f"Supported chains: {', '.join(sorted(SUPPORTED_CHAINS))}"
        )

    if not address.startswith("0x"):
        raise ValueError("Address must start with 0x")

    if entity_type not in SUPPORTED_ENTITY_TYPES:
        raise ValueError(
            f"Unsupported entity_type: {entity_type}. "
            f"Supported types: {', '.join(sorted(SUPPORTED_ENTITY_TYPES))}"
        )

    if confidence is not None and not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be between 0 and 1")

    result = create_risk_entity(
        address=address,
        chain=chain,
        entity_type=entity_type,
        name=name,
        source=source,
        risk_category=risk_category,
        confidence=confidence,
        evidence=evidence,
        updated_at=updated_at,
    )

    if result is None:
        raise ValueError("Failed to create risk entity")

    return dict(result)

def get_intelligence_risk_entities(
    chain: str | None = None,
    entity_type: str | None = None,
    source: str | None = None,
    risk_category: str | None = None,
):
    chain = chain.lower() if chain else None
    entity_type = entity_type.lower() if entity_type else None
    source = source.lower() if source else None
    risk_category = (
        risk_category.lower()
        if risk_category
        else None
    )

    return list_risk_entities(
        chain=chain,
        entity_type=entity_type,
        source=source,
        risk_category=risk_category,
    )


def get_intelligence_risk_entity(
    address: str,
    chain: str,
):
    chain = chain.lower()

    if chain not in SUPPORTED_CHAINS:
        raise ValueError(
            f"Unsupported chain: {chain}. "
            f"Supported chains: {', '.join(sorted(SUPPORTED_CHAINS))}"
        )

    if not address.startswith("0x"):
        raise ValueError("Address must start with 0x")

    result = get_risk_entity(
        address=address,
        chain=chain,
    )

    if result is None:
        raise ValueError(
            "Risk entity not found"
        )

    return result

def update_intelligence_risk_entity(
    address: str,
    chain: str,
    entity_type: str | None = None,
    name: str | None = None,
    source: str | None = None,
    risk_category: str | None = None,
    confidence: float | None = None,
    evidence: str | None = None,
    updated_at: str | None = None,
):
    chain = chain.lower()

    if chain not in SUPPORTED_CHAINS:
        raise ValueError(
            f"Unsupported chain: {chain}. "
            f"Supported chains: {', '.join(sorted(SUPPORTED_CHAINS))}"
        )

    if not address.startswith("0x"):
        raise ValueError("Address must start with 0x")

    if entity_type is not None:
        entity_type = entity_type.lower().strip()

        if entity_type not in SUPPORTED_ENTITY_TYPES:
            raise ValueError(
                f"Unsupported entity_type: {entity_type}. "
                f"Supported types: {', '.join(sorted(SUPPORTED_ENTITY_TYPES))}"
            )

    if source is not None:
        source = source.lower().strip()

    if risk_category is not None:
        risk_category = risk_category.lower().strip()

    if confidence is not None and not 0.0 <= confidence <= 1.0:
        raise ValueError(
            "confidence must be between 0 and 1"
        )

    result = update_risk_entity(
        address=address,
        chain=chain,
        entity_type=entity_type,
        name=name,
        source=source,
        risk_category=risk_category,
        confidence=confidence,
        evidence=evidence,
        updated_at=updated_at,
    )

    if result is None:
        raise ValueError(
            "Risk entity not found"
        )

    return result

def delete_intelligence_risk_entity(
    address: str,
    chain: str,
):
    chain = chain.lower()

    if chain not in SUPPORTED_CHAINS:
        raise ValueError(
            f"Unsupported chain: {chain}. "
            f"Supported chains: {', '.join(sorted(SUPPORTED_CHAINS))}"
        )

    if not address.startswith("0x"):
        raise ValueError("Address must start with 0x")

    deleted = delete_risk_entity(
        address=address,
        chain=chain,
    )

    if deleted == 0:
        raise ValueError(
            "Risk entity not found"
        )

    return {
        "message": "Risk entity deleted successfully",
        "address": address,
        "chain": chain,
    }