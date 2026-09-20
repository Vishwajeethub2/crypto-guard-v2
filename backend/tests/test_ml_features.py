from app.services.ml_features import build_ml_features


def test_build_ml_features():

    behavior = {
        "incoming_transaction_count": 2,
        "outgoing_transaction_count": 5,
        "incoming_value": 500.0,
        "outgoing_value": 1000.0,
    }

    graph = {
        "incoming_connections": 2,
        "outgoing_connections": 4,
        "fan_in": 2,
        "fan_out": 4,
        "outgoing_concentration": 0.8,
        "incoming_concentration": 0.5,
        "multi_hop_exposure_count": 1,
        "top_outgoing_counterparties": [
            {
                "transaction_count": 3,
            }
        ],
        "top_incoming_counterparties": [],
    }

    timeline = {
        "activity_duration_seconds": 10000,
        "average_transaction_gap_seconds": 2000,
        "shortest_transaction_gap_seconds": 300,
        "longest_transaction_gap_seconds": 5000,
        "bursts": [
            {
                "transaction_count": 3,
            }
        ],
        "temporal_signals": [
            {
                "signal": "rapid_transaction_sequence",
            }
        ],
    }

    features = build_ml_features(
        behavior,
        graph,
        timeline,
    )

    assert features[
        "transaction_count"
    ] == 7

    assert features[
        "incoming_transaction_count"
    ] == 2

    assert features[
        "outgoing_transaction_count"
    ] == 5

    assert features[
        "total_incoming_value"
    ] == 500

    assert features[
        "total_outgoing_value"
    ] == 1000

    assert features[
        "incoming_outgoing_value_ratio"
    ] == 0.5

    assert features[
        "transaction_burst_count"
    ] == 1

    assert features[
        "rapid_transaction_sequence_count"
    ] == 1

    assert features[
        "counterparty_reuse_count"
    ] == 1