from app.services.vasp_attribution import analyze_vasp_attribution


def test_vasp_attribution_finds_coinbase_at_two_hops():
    result = analyze_vasp_attribution(
        address="0x0000000000000000000000000000000000000000",
        chain="ethereum",
        max_hops=2,
    )

    candidates = result["candidates"]

    coinbase_candidates = [
        candidate
        for candidate in candidates
        if candidate["name"] == "Coinbase"
    ]

    assert coinbase_candidates, "Coinbase VASP attribution was not found"

    coinbase = coinbase_candidates[0]

    assert coinbase["hop"] == 2
    assert coinbase["attribution_basis"] == "transaction_path_match"
    assert coinbase["confidence"] == 0.95
from app.services.vasp_attribution import analyze_vasp_attribution


def test_vasp_attribution_returns_no_candidate_for_unknown_wallet():
    result = analyze_vasp_attribution(
        address="0x1111111111111111111111111111111111111111",
        chain="ethereum",
        max_hops=2,
    )

    assert result["candidate_count"] == 0
    assert result["candidates"] == []
