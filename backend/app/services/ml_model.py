from pathlib import Path
from typing import Any

import joblib
import pandas as pd


# Project root:
# CRYPTO guard v2/
PROJECT_ROOT = Path(__file__).resolve().parents[3]

MODEL_PATH = (
    PROJECT_ROOT
    / "ml"
    / "models"
    / "crypto_guard_risk_v1.joblib"
)


class CryptoGuardMLModel:
    def __init__(self, model_path: Path = MODEL_PATH):
        self.model_path = model_path

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"ML model not found: {self.model_path}"
            )

        bundle = joblib.load(self.model_path)

        if not isinstance(bundle, dict):
            raise ValueError(
                "Invalid ML model bundle: expected a dictionary."
            )

        required_keys = {
            "model",
            "features",
            "schema_version",
            "model_version",
        }

        missing_keys = required_keys - set(bundle.keys())

        if missing_keys:
            raise ValueError(
                f"Invalid ML model bundle. Missing keys: {sorted(missing_keys)}"
            )

        self.model = bundle["model"]
        self.features = bundle["features"]
        self.schema_version = str(bundle["schema_version"])
        self.model_version = str(bundle["model_version"])

    def prepare_features(
        self,
        features: dict[str, Any],
    ) -> pd.DataFrame:
        missing_features = [
            feature
            for feature in self.features
            if feature not in features
        ]

        if missing_features:
            raise ValueError(
                f"Missing ML features: {missing_features}"
            )

        row = {
            feature: features[feature]
            for feature in self.features
        }

        return pd.DataFrame(
            [row],
            columns=self.features,
        )

    def predict(
        self,
        features: dict[str, Any],
    ) -> dict[str, Any]:

        # ------------------------------------------------------
        # Only the trained model features are sent to the model.
        # This keeps the existing 14-feature model unchanged.
        # ------------------------------------------------------

        X = self.prepare_features(features)

        prediction = int(
            self.model.predict(X)[0]
        )

        probabilities = self.model.predict_proba(X)[0]

        probability = float(
            probabilities[1]
        )

        # ------------------------------------------------------
        # Features actually used by the trained ML model.
        # ------------------------------------------------------

        model_feature_values = {
            feature: features[feature]
            for feature in self.features
        }

        # ------------------------------------------------------
        # Additional analytical features calculated by
        # Crypto Guard but not currently part of the trained
        # model schema.
        #
        # Example:
        # maximum_incoming_value
        # ------------------------------------------------------

        additional_feature_values = {
            feature: value
            for feature, value in features.items()
            if feature not in self.features
        }

        # ------------------------------------------------------
        # Return prediction + complete analytical feature set.
        # ------------------------------------------------------

        return {
            "prediction": prediction,
            "probability": probability,
            "model_version": self.model_version,
            "schema_version": self.schema_version,
            "features_used": self.features,
            "feature_values": {
                **model_feature_values,
                **additional_feature_values,
            },
        }


_model_instance: CryptoGuardMLModel | None = None


def get_ml_model() -> CryptoGuardMLModel:

    global _model_instance

    if _model_instance is None:
        _model_instance = CryptoGuardMLModel()

    return _model_instance