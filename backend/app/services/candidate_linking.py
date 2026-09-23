from __future__ import annotations

from typing import Any

from app.services.vasp_attribution import analyze_vasp_attribution


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_link_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    hop = candidate.get("hop")
    confidence = _safe_float(candidate.get("confidence"))

    wallets = candidate.get("wallets") or []
    transfers = candidate.get("transfers") or []

    signals: list[str] = []

    if hop == 0:
        signals.append("Direct address match")
    elif hop is not None:
        signals.append(
            f"Transaction-path match at {hop}-hop distance"
        )

    if candidate.get("source"):
        signals.append("Known VASP intelligence source")

    if candidate.get("risk_category"):
        signals.append("Risk category available")

    if wallets:
        signals.append(
            f"Connected wallet evidence available ({len(wallets)})"
        )

    if transfers:
        signals.append(
            f"Transfer evidence available ({len(transfers)})"
        )

    if confidence is not None:
        signals.append("Existing intelligence confidence available")

    if hop == 0:
        link_basis = "direct_address_match"
    elif hop is not None:
        link_basis = "transaction_path_match"
    else:
        link_basis = "intelligence_match"

    if hop == 0:
        link_strength = "direct"
    elif hop == 1:
        link_strength = "near_path"
    elif hop == 2:
        link_strength = "extended_path"
    else:
        link_strength = "research_candidate"

    return {
        "name": candidate.get("name"),
        "address": candidate.get("address"),
        "chain": candidate.get("chain"),
        "source": candidate.get("source"),
        "risk_category": candidate.get("risk_category"),
        "confidence": confidence,
        "hop": hop,
        "link_basis": link_basis,
        "link_strength": link_strength,
        "signals": signals,
        "signal_count": len(signals),
        "evidence": candidate.get("evidence"),
        "wallets": wallets,
        "transfers": transfers,
        "reason": candidate.get("reason"),
    }


def analyze_candidate_linking(
    *,
    address: str,
    chain: str,
    max_hops: int = 2,
) -> dict[str, Any]:
    if max_hops < 0:
        raise ValueError("max_hops cannot be negative")

    if max_hops > 2:
        raise ValueError(
            "max_hops cannot exceed 2 for candidate linking"
        )

    chain = chain.lower().strip()

    attribution = analyze_vasp_attribution(
        address=address,
        chain=chain,
        max_hops=max_hops,
    )

    candidates = [
        _build_link_candidate(candidate)
        for candidate in attribution.get("candidates", [])
    ]

    candidates.sort(
        key=lambda candidate: (
            candidate.get("hop")
            if candidate.get("hop") is not None
            else 999,
            -(
                candidate.get("confidence")
                if candidate.get("confidence") is not None
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
            "Candidate linking built from existing VASP "
            "intelligence attribution and transaction-path "
            "evidence."
        ),
        "notice": (
            "Candidate links are research-stage intelligence "
            "assessments. A candidate link does not establish "
            "ownership, control, legal attribution, or illicit "
            "activity."
        ),
    }