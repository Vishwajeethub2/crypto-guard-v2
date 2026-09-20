from __future__ import annotations

from typing import Any


def _collect_signals(
    graph: dict[str, Any],
    timeline: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Collect existing analytical signals without changing
    their original meaning or severity.
    """

    signals: list[dict[str, Any]] = []

    graph_signals = graph.get(
        "graph_signals",
        [],
    )

    timeline_signals = timeline.get(
        "temporal_signals",
        [],
    )

    for signal in graph_signals:
        if isinstance(signal, dict):
            signals.append(
                {
                    "source": "graph",
                    **signal,
                }
            )

    for signal in timeline_signals:
        if isinstance(signal, dict):
            signals.append(
                {
                    "source": "timeline",
                    **signal,
                }
            )

    return signals


def build_aml_evidence_assessment(
    *,
    graph: dict[str, Any],
    timeline: dict[str, Any],
    ml_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Build an analyst-reviewable AML evidence assessment.

    This function does not make a definitive illicit-activity
    determination and does not treat the research-stage ML
    probability as a validated AML probability.
    """

    signals = _collect_signals(
        graph=graph,
        timeline=timeline,
    )

    indicators = [
        signal["signal"]
        for signal in signals
        if signal.get("signal")
    ]

    high_severity_count = sum(
        1
        for signal in signals
        if str(
            signal.get("severity", "")
        ).lower() == "high"
    )

    medium_severity_count = sum(
        1
        for signal in signals
        if str(
            signal.get("severity", "")
        ).lower() == "medium"
    )

    if signals:
        review_status = "requires_review"
    else:
        review_status = "no_indicators_detected"

    return {
        "assessment_type": (
            "research_analyst_assessment"
        ),
        "review_status": review_status,
        "indicator_count": len(indicators),
        "high_severity_indicator_count": (
            high_severity_count
        ),
        "medium_severity_indicator_count": (
            medium_severity_count
        ),
        "indicators": indicators,
        "signals": signals,
        "ml": {
            "prediction": ml_result.get(
                "prediction"
            ),
            "probability": ml_result.get(
                "probability"
            ),
            "model_version": ml_result.get(
                "model_version"
            ),
            "schema_version": ml_result.get(
                "schema_version"
            ),
        },
        "notice": (
            "This is a research-stage evidence assessment "
            "for analyst review. It is not a definitive "
            "determination of illicit activity or AML status."
        ),
    }