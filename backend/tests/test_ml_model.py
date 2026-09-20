from app.services.ml_model import (
    CryptoGuardMLModel,
)


def test_ml_model_loads():

    model = CryptoGuardMLModel()

    assert model.model is not None

    assert model.model_version == "1.0"

    assert model.schema_version == "1.0"

    assert len(
        model.features
    ) > 0


def test_ml_model_prediction():

    model = CryptoGuardMLModel()

    feature_values = {
        feature: 0.0
        for feature in model.features
    }

    feature_values[
        "transaction_count"
    ] = 5.0

    feature_values[
        "incoming_transaction_count"
    ] = 2.0

    feature_values[
        "outgoing_transaction_count"
    ] = 3.0

    feature_values[
        "total_incoming_value"
    ] = 100.0

    feature_values[
        "total_outgoing_value"
    ] = 200.0

    result = model.predict(
        feature_values
    )

    assert "prediction" in result

    assert "probability" in result

    assert "model_version" in result

    assert "schema_version" in result

    assert 0.0 <= result[
        "probability"
    ] <= 1.0

    assert result[
        "prediction"
    ] in {0, 1}

    assert len(
        result["features_used"]
    ) == len(
        model.features
    )