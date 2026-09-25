from __future__ import annotations

from typing import Any

from app.db.neo4j import get_risk_entity_exposure


def _get_hop_proximity_score(hop: int | None) -> float:
    """
    Heuristic proximity score.

    This is NOT a probability of ownership or control.
    It only represents how close the known intelligence
    entity is to the investigated wallet.
    """
    if hop == 0:
        return 1.0

    if hop == 1:
        return 0.85

    if hop == 2:
        return 0.70

    return 0.50


def _get_match_strength(hop: int | None) -> str:
    if hop == 0:
        return "direct"

    if hop == 1:
        return "strong_path"

    if hop == 2:
        return "indirect_path"

    return "unknown"


def _calculate_attribution_score(
    confidence: float | None,
    hop: int | None,
) -> float:
    """
    Calculate a deterministic research-stage attribution score.

    70% comes from the intelligence confidence.
    30% comes from transaction-path proximity.

    The result is a ranking signal, NOT a probability.
    """
    intelligence_confidence = (
        confidence
        if confidence is not None
        else 0.0
    )

    intelligence_confidence = max(
        0.0,
        min(
            1.0,
            float(intelligence_confidence),
        ),
    )

    hop_proximity = _get_hop_proximity_score(hop)

    score = (
        (intelligence_confidence * 0.70)
        + (hop_proximity * 0.30)
    )

    return round(score, 4)


def _build_reason(
    *,
    entity_name: str | None,
    hop: int | None,
    confidence: float | None,
) -> str:
    name = entity_name or "known VASP"

    if hop == 0:
        return (
            f"The investigated wallet directly matches "
            f"a known {name} VASP intelligence entity. "
            f"The intelligence confidence is "
            f"{confidence:.2f}."
            if confidence is not None
            else
            f"The investigated wallet directly matches "
            f"a known {name} VASP intelligence entity."
        )

    if hop == 1:
        return (
            f"A known {name} VASP address is connected "
            f"through a 1-hop transaction path from the "
            f"investigated wallet. "
            f"The intelligence confidence is "
            f"{confidence:.2f}."
            if confidence is not None
            else
            f"A known {name} VASP address is connected "
            f"through a 1-hop transaction path from the "
            f"investigated wallet."
        )

    if hop == 2:
        return (
            f"A known {name} VASP address is connected "
            f"through a 2-hop transaction path from the "
            f"investigated wallet. "
            f"The intelligence confidence is "
            f"{confidence:.2f}."
            if confidence is not None
            else
            f"A known {name} VASP address is connected "
            f"through a 2-hop transaction path from the "
            f"investigated wallet."
        )

    return (
        f"A known {name} VASP intelligence entity was "
        f"identified, but the transaction-path distance "
        f"could not be determined."
    )


def analyze_vasp_attribution(
    *,
    address: str,
    chain: str,
    max_hops: int = 2,
) -> dict[str, Any]:
    if max_hops < 0:
        raise ValueError(
            "max_hops cannot be negative"
        )

    if max_hops > 2:
        raise ValueError(
            "max_hops cannot exceed 2 for the current implementation"
        )

    address = address.strip()
    chain = chain.lower().strip()

    if not address:
        raise ValueError(
            "address is required"
        )

    if not chain:
        raise ValueError(
            "chain is required"
        )

    exposures = get_risk_entity_exposure(
        address=address,
        chain=chain,
        max_hops=max_hops,
    )

    candidates: list[dict[str, Any]] = []

    for exposure in exposures:
        if (
            str(
                exposure.get(
                    "entity_type",
                    "",
                )
            ).lower()
            != "vasp"
        ):
            continue

        hop = exposure.get("hop_count")

        confidence = exposure.get(
            "confidence"
        )

        attribution_score = (
            _calculate_attribution_score(
                confidence=confidence,
                hop=hop,
            )
        )

        hop_proximity_score = (
            _get_hop_proximity_score(hop)
        )

        match_strength = _get_match_strength(
            hop
        )

        candidates.append(
            {
                "name": exposure.get(
                    "entity_name"
                ),
                "address": exposure.get(
                    "risk_entity_address"
                ),
                "chain": exposure.get(
                    "risk_entity_chain"
                ),
                "source": exposure.get(
                    "source"
                ),
                "risk_category": exposure.get(
                    "risk_category"
                ),

                # Original intelligence confidence.
                "confidence": confidence,

                # Explicit name makes its purpose clearer
                # for API consumers.
                "intelligence_confidence": confidence,

                # Research-stage heuristic ranking signal.
                "attribution_score": attribution_score,

                "hop_proximity_score": (
                    hop_proximity_score
                ),

                "match_strength": match_strength,

                "evidence": exposure.get(
                    "evidence"
                ),

                "hop": hop,

                "attribution_basis": (
                    "direct_address_match"
                    if hop == 0
                    else "transaction_path_match"
                ),

                "reason": _build_reason(
                    entity_name=exposure.get(
                        "entity_name"
                    ),
                    hop=hop,
                    confidence=confidence,
                ),

                "wallets": exposure.get(
                    "wallets",
                    [],
                ),

                "transfers": exposure.get(
                    "transfers",
                    [],
                ),
            }
        )

    candidates.sort(
        key=lambda candidate: (
            -float(
                candidate.get(
                    "attribution_score",
                    0.0,
                )
                or 0.0
            ),
            candidate.get(
                "hop"
            )
            if candidate.get("hop") is not None
            else 999,
            -float(
                candidate.get(
                    "confidence",
                    0.0,
                )
                or 0.0
            ),
            str(
                candidate.get(
                    "address",
                    "",
                )
            ).lower(),
        )
    )

    return {
        "address": address,
        "chain": chain,
        "max_hops": max_hops,
        "status": (
            "candidates_found"
            if candidates
            else "no_candidates_found"
        ),
        "candidate_count": len(
            candidates
        ),
        "candidates": candidates,
        "method": (
            "Known VASP intelligence matching "
            "against transaction-connected "
            "RiskEntity records, ranked using "
            "intelligence confidence and "
            "transaction-path proximity."
        ),
        "notice": (
            "VASP attribution is a research-stage "
            "intelligence assessment. The "
            "attribution score is a heuristic "
            "ranking signal, not a probability. "
            "A direct or transaction-path match "
            "does not by itself establish ownership, "
            "control, or illicit activity."
        ),
    }