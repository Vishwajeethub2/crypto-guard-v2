from __future__ import annotations

from typing import Any

from app.db.neo4j import get_risk_entity_exposure


def analyze_vasp_attribution(
    *,
    address: str,
    chain: str,
    max_hops: int = 2,
) -> dict[str, Any]:
    if max_hops < 0:
        raise ValueError("max_hops cannot be negative")

    if max_hops > 2:
        raise ValueError(
            "max_hops cannot exceed 2 for the current implementation"
        )

    chain = chain.lower().strip()

    exposures = get_risk_entity_exposure(
        address=address,
        chain=chain,
        max_hops=max_hops,
    )

    candidates = []

    for exposure in exposures:
        if str(
            exposure.get("entity_type", "")
        ).lower() != "vasp":
            continue

        hop = exposure.get("hop_count")

        if hop == 0:
            attribution_basis = "direct_address_match"
            reason = (
                "The investigated wallet is directly "
                "associated with a known VASP intelligence "
                "entity."
            )
        else:
            attribution_basis = "transaction_path_match"
            reason = (
                f"A known VASP address was reached through "
                f"a {hop}-hop transaction path from the "
                f"investigated wallet."
            )

        candidates.append(
            {
                "name": exposure.get("entity_name"),
                "address": exposure.get(
                    "risk_entity_address"
                ),
                "chain": exposure.get(
                    "risk_entity_chain"
                ),
                "source": exposure.get("source"),
                "risk_category": exposure.get(
                    "risk_category"
                ),
                "confidence": exposure.get(
                    "confidence"
                ),
                "evidence": exposure.get("evidence"),
                "hop": hop,
                "attribution_basis": attribution_basis,
                "reason": reason,
                "wallets": exposure.get(
                    "wallets", []
                ),
                "transfers": exposure.get(
                    "transfers", []
                ),
            }
        )

    candidates.sort(
        key=lambda candidate: (
            candidate.get("hop")
            if candidate.get("hop") is not None
            else 999,
            -(
                candidate.get("confidence")
                if candidate.get("confidence")
                is not None
                else 0.0
            ),
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
        "candidate_count": len(candidates),
        "candidates": candidates,
        "method": (
            "Known VASP intelligence matching against "
            "transaction-connected RiskEntity records."
        ),
        "notice": (
            "VASP attribution is a research-stage "
            "intelligence assessment. A transaction-path "
            "match does not by itself establish ownership, "
            "control, or illicit activity."
        ),
    }