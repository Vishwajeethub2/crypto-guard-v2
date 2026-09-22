from pathlib import Path
from datetime import datetime, timezone
import json

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split


DATA_PATH = Path(
    "ml/datasets/processed/ethereum_fraud/crypto_guard_features_v1.csv"
)

SCHEMA_PATH = Path(
    "ml/feature_schema/crypto_guard_features_v1.json"
)

MODEL_DIR = Path(
    "ml/models"
)

MODEL_PATH = (
    MODEL_DIR
    / "crypto_guard_risk_v1.joblib"
)

METADATA_PATH = (
    MODEL_DIR
    / "crypto_guard_risk_v1_metadata.json"
)

RANDOM_STATE = 42


def main() -> None:

    print("=" * 75)
    print("CRYPTO GUARD ML MODEL TRAINING")
    print("=" * 75)

    # ------------------------------------------------------------
    # Check files
    # ------------------------------------------------------------

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found:\n{DATA_PATH}"
        )

    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Schema not found:\n{SCHEMA_PATH}"
        )

    # ------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------

    print("\nLoading feature dataset...")

    df = pd.read_csv(
        DATA_PATH
    )

    print(
        f"Rows:    {len(df):,}"
    )

    print(
        f"Columns: {len(df.columns):,}"
    )

    # ------------------------------------------------------------
    # Load schema
    # ------------------------------------------------------------

    with SCHEMA_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:

        schema = json.load(file)

    schema_features = []

    for group_features in (
        schema["groups"].values()
    ):
        for feature in group_features:
            schema_features.append(
                feature["name"]
            )

    # ------------------------------------------------------------
    # Validate schema
    # ------------------------------------------------------------

    missing_features = [
        feature
        for feature in schema_features
        if feature not in df.columns
    ]

    if missing_features:
        raise ValueError(
            "Dataset is missing schema features:\n"
            + "\n".join(
                missing_features
            )
        )

    print(
        f"Schema features: "
        f"{len(schema_features)}"
    )

    # ------------------------------------------------------------
    # Detect constant features
    # ------------------------------------------------------------

    feature_variance = df[
        schema_features
    ].var()

    constant_features = [
        feature
        for feature in schema_features
        if feature_variance[feature] == 0
    ]

    usable_features = [
        feature
        for feature in schema_features
        if feature not in constant_features
    ]

    print("\n" + "-" * 75)
    print("FEATURE AVAILABILITY")
    print("-" * 75)

    print(
        f"Schema features:   "
        f"{len(schema_features)}"
    )

    print(
        f"Constant features: "
        f"{len(constant_features)}"
    )

    print(
        f"Usable features:   "
        f"{len(usable_features)}"
    )

    if constant_features:

        print(
            "\nConstant features excluded "
            "from this training run:"
        )

        for feature in constant_features:
            print(
                f"  - {feature}"
            )

    # ------------------------------------------------------------
    # Target
    # ------------------------------------------------------------

    if "target" not in df.columns:
        raise ValueError(
            "Target column not found."
        )

    X = df[
        usable_features
    ].copy()

    y = df[
        "target"
    ].astype(int)

    print("\n" + "-" * 75)
    print("TARGET DISTRIBUTION")
    print("-" * 75)

    print(
        y.value_counts()
        .sort_index()
    )

    print(
        "\nTarget percentages:"
    )

    print(
        (
            y.value_counts(
                normalize=True
            )
            .sort_index()
            * 100
        ).round(2)
    )

    # ------------------------------------------------------------
    # Safety checks
    # ------------------------------------------------------------

    if X.isna().sum().sum() != 0:
        raise ValueError(
            "Missing values found."
        )

    if np.isinf(
        X.to_numpy()
    ).sum() != 0:
        raise ValueError(
            "Infinite values found."
        )

    # ------------------------------------------------------------
    # Train / validation / test split
    # ------------------------------------------------------------

    print("\n" + "-" * 75)
    print("DATA SPLIT")
    print("-" * 75)

    X_train_full, X_test, y_train_full, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.20,
            stratify=y,
            random_state=RANDOM_STATE,
        )
    )

    X_train, X_validation, y_train, y_validation = (
        train_test_split(
            X_train_full,
            y_train_full,
            test_size=0.20,
            stratify=y_train_full,
            random_state=RANDOM_STATE,
        )
    )

    print(
        f"Training:   {len(X_train):,}"
    )

    print(
        f"Validation: {len(X_validation):,}"
    )

    print(
        f"Test:       {len(X_test):,}"
    )

    # ------------------------------------------------------------
    # Train candidate model
    # ------------------------------------------------------------

    print("\n" + "-" * 75)
    print("TRAINING RANDOM FOREST")
    print("-" * 75)

    model = RandomForestClassifier(
        n_estimators=500,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,
        max_features="sqrt",
    )

    print(
        "Trees:       500"
    )

    print(
        "Class weight: balanced"
    )

    print(
        "Max features: sqrt"
    )

    print(
        "\nTraining..."
    )

    model.fit(
        X_train,
        y_train,
    )

    print(
        "Training complete."
    )

    # ------------------------------------------------------------
    # Validation evaluation
    # ------------------------------------------------------------

    print("\n" + "-" * 75)
    print("VALIDATION PERFORMANCE")
    print("-" * 75)

    validation_probabilities = (
        model.predict_proba(
            X_validation
        )[:, 1]
    )

    validation_predictions = (
        validation_probabilities >= 0.5
    ).astype(int)

    validation_metrics = {
        "accuracy": accuracy_score(
            y_validation,
            validation_predictions,
        ),
        "precision": precision_score(
            y_validation,
            validation_predictions,
            zero_division=0,
        ),
        "recall": recall_score(
            y_validation,
            validation_predictions,
            zero_division=0,
        ),
        "f1": f1_score(
            y_validation,
            validation_predictions,
            zero_division=0,
        ),
        "roc_auc": roc_auc_score(
            y_validation,
            validation_probabilities,
        ),
        "pr_auc": average_precision_score(
            y_validation,
            validation_probabilities,
        ),
    }

    for metric, value in (
        validation_metrics.items()
    ):
        print(
            f"{metric.upper():<12}"
            f"{value:.4f}"
        )

    # ------------------------------------------------------------
    # Final test evaluation
    # ------------------------------------------------------------

    print("\n" + "-" * 75)
    print("FINAL HOLDOUT TEST PERFORMANCE")
    print("-" * 75)

    test_probabilities = (
        model.predict_proba(
            X_test
        )[:, 1]
    )

    test_predictions = (
        test_probabilities >= 0.5
    ).astype(int)

    test_metrics = {
        "accuracy": accuracy_score(
            y_test,
            test_predictions,
        ),
        "precision": precision_score(
            y_test,
            test_predictions,
            zero_division=0,
        ),
        "recall": recall_score(
            y_test,
            test_predictions,
            zero_division=0,
        ),
        "f1": f1_score(
            y_test,
            test_predictions,
            zero_division=0,
        ),
        "roc_auc": roc_auc_score(
            y_test,
            test_probabilities,
        ),
        "pr_auc": average_precision_score(
            y_test,
            test_probabilities,
        ),
    }

    for metric, value in (
        test_metrics.items()
    ):
        print(
            f"{metric.upper():<12}"
            f"{value:.4f}"
        )

    # ------------------------------------------------------------
    # Confusion matrix
    # ------------------------------------------------------------

    print("\nConfusion matrix:")

    print(
        confusion_matrix(
            y_test,
            test_predictions,
        )
    )

    print("\nClassification report:")

    print(
        classification_report(
            y_test,
            test_predictions,
            digits=4,
            zero_division=0,
        )
    )

    # ------------------------------------------------------------
    # Feature importance
    # ------------------------------------------------------------

    print("\n" + "-" * 75)
    print("TOP MODEL FEATURES")
    print("-" * 75)

    importance = (
        pd.DataFrame(
            {
                "feature": usable_features,
                "importance": (
                    model.feature_importances_
                ),
            }
        )
        .sort_values(
            "importance",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    for rank, (_, row) in enumerate(
        importance.head(20).iterrows(),
        start=1,
    ):

        print(
            f"{rank:2d}. "
            f"{row['importance']:.6f}  "
            f"{row['feature']}"
        )

    # ------------------------------------------------------------
    # Save model
    # ------------------------------------------------------------

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    model_bundle = {
        "model": model,
        "features": usable_features,
        "schema_version": schema[
            "schema_version"
        ],
        "model_version": "1.0",
    }

    joblib.dump(
        model_bundle,
        MODEL_PATH,
    )

    # ------------------------------------------------------------
    # Save metadata
    # ------------------------------------------------------------

    metadata = {
        "model_version": "1.0",
        "schema_version": schema[
            "schema_version"
        ],
        "model_type": "RandomForestClassifier",
        "training_dataset": str(
            DATA_PATH
        ),
        "training_rows": int(
            len(X_train)
        ),
        "validation_rows": int(
            len(X_validation)
        ),
        "test_rows": int(
            len(X_test)
        ),
        "schema_feature_count": int(
            len(schema_features)
        ),
        "usable_feature_count": int(
            len(usable_features)
        ),
        "excluded_constant_features": (
            constant_features
        ),
        "random_state": RANDOM_STATE,
        "n_estimators": 500,
        "class_weight": "balanced",
        "max_features": "sqrt",
        "validation_metrics": {
            key: float(value)
            for key, value in (
                validation_metrics.items()
            )
        },
        "test_metrics": {
            key: float(value)
            for key, value in (
                test_metrics.items()
            )
        },
        "classification_threshold": 0.5,
        "trained_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "status": "research_candidate",
        "warning": (
            "This model is a research candidate trained "
            "on a labeled Ethereum wallet dataset. "
            "It is not a validated production AML probability "
            "or definitive illicit-activity determination."
        ),
    }

    with METADATA_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metadata,
            file,
            indent=2,
        )

    print("\n" + "=" * 75)
    print("MODEL ARTIFACTS SAVED")
    print("=" * 75)

    print(
        f"\nModel:\n  {MODEL_PATH}"
    )

    print(
        f"\nMetadata:\n  {METADATA_PATH}"
    )

    print("\n" + "=" * 75)
    print("CRYPTO GUARD MODEL TRAINING COMPLETE")
    print("=" * 75)


if __name__ == "__main__":
    main()