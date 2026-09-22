from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.calibration import (
    CalibratedClassifierCV,
    calibration_curve,
)
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = (
    PROJECT_ROOT
    / "ml"
    / "datasets"
    / "processed"
    / "ethereum_fraud"
    / "ethereum_fraud_model_ready.csv"
)


TARGET = "FLAG"

TOKEN_COLUMNS = [
    "ERC20 most sent token type",
    "ERC20_most_rec_token_type",
]

RANDOM_STATE = 42


# =========================================================
# Load dataset
# =========================================================

df = pd.read_csv(INPUT_PATH)

print("=" * 80)
print("MODEL PROBABILITY CALIBRATION")
print("=" * 80)

print()
print("Dataset shape:", df.shape)


# =========================================================
# Prepare behavioral features
# =========================================================

X = df.drop(
    columns=[TARGET] + TOKEN_COLUMNS,
    errors="ignore",
)

X = X.select_dtypes(
    include=["number"]
)

y = df[TARGET]


# =========================================================
# Train / calibration / test split
# =========================================================
#
# We use three separate portions:
#
# Training set     -> train the Random Forest
# Calibration set  -> learn probability calibration
# Test set         -> final evaluation
#
# This prevents the calibration step from learning
# directly from the final test data.
# =========================================================

X_train_full, X_test, y_train_full, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=RANDOM_STATE,
    stratify=y,
)

X_train, X_calibration, y_train, y_calibration = train_test_split(
    X_train_full,
    y_train_full,
    test_size=0.25,
    random_state=RANDOM_STATE,
    stratify=y_train_full,
)


print()
print("Training rows   :", len(X_train))
print("Calibration rows:", len(X_calibration))
print("Testing rows    :", len(X_test))


# =========================================================
# Base Random Forest
# =========================================================

base_model = RandomForestClassifier(
    n_estimators=300,
    random_state=RANDOM_STATE,
    n_jobs=-1,
    class_weight="balanced",
)

print()
print("Training base Random Forest...")

base_model.fit(
    X_train,
    y_train,
)


# =========================================================
# Base probabilities
# =========================================================

base_probabilities = base_model.predict_proba(
    X_test
)[:, 1]


# =========================================================
# Calibration models
# =========================================================

print()
print("Training sigmoid calibration...")

sigmoid_model = CalibratedClassifierCV(
    estimator=RandomForestClassifier(
        n_estimators=300,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        class_weight="balanced",
    ),
    method="sigmoid",
    cv=5,
)

sigmoid_model.fit(
    X_train_full,
    y_train_full,
)

sigmoid_probabilities = sigmoid_model.predict_proba(
    X_test
)[:, 1]


print("Training isotonic calibration...")

isotonic_model = CalibratedClassifierCV(
    estimator=RandomForestClassifier(
        n_estimators=300,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        class_weight="balanced",
    ),
    method="isotonic",
    cv=5,
)

isotonic_model.fit(
    X_train_full,
    y_train_full,
)

isotonic_probabilities = isotonic_model.predict_proba(
    X_test
)[:, 1]


# =========================================================
# Evaluation helper
# =========================================================

def evaluate_probabilities(
    name,
    probabilities,
):
    predictions = (
        probabilities >= 0.50
    ).astype(int)

    precision = precision_score(
        y_test,
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        y_test,
        predictions,
        zero_division=0,
    )

    f1 = f1_score(
        y_test,
        predictions,
        zero_division=0,
    )

    roc_auc = roc_auc_score(
        y_test,
        probabilities,
    )

    pr_auc = average_precision_score(
        y_test,
        probabilities,
    )

    brier = brier_score_loss(
        y_test,
        probabilities,
    )

    print()
    print(name)

    print(
        f"  Precision : {precision:.4f}"
    )

    print(
        f"  Recall    : {recall:.4f}"
    )

    print(
        f"  F1        : {f1:.4f}"
    )

    print(
        f"  ROC-AUC   : {roc_auc:.4f}"
    )

    print(
        f"  PR-AUC    : {pr_auc:.4f}"
    )

    print(
        f"  Brier     : {brier:.4f}"
    )

    return {
        "model": name,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "brier": brier,
    }


# =========================================================
# Evaluate models
# =========================================================

print()
print("=" * 80)
print("MODEL COMPARISON")
print("=" * 80)

results = []

results.append(
    evaluate_probabilities(
        "Uncalibrated Random Forest",
        base_probabilities,
    )
)

results.append(
    evaluate_probabilities(
        "Sigmoid Calibrated Random Forest",
        sigmoid_probabilities,
    )
)

results.append(
    evaluate_probabilities(
        "Isotonic Calibrated Random Forest",
        isotonic_probabilities,
    )
)


# =========================================================
# Calibration curves
# =========================================================

print()
print("=" * 80)
print("CALIBRATION CURVES")
print("=" * 80)

for name, probabilities in [
    (
        "Uncalibrated",
        base_probabilities,
    ),
    (
        "Sigmoid",
        sigmoid_probabilities,
    ),
    (
        "Isotonic",
        isotonic_probabilities,
    ),
]:

    fraction_positive, mean_prediction = calibration_curve(
        y_test,
        probabilities,
        n_bins=10,
        strategy="quantile",
    )

    print()
    print(name)

    print(
        "Mean predicted probability:",
        np.round(
            mean_prediction,
            4,
        ),
    )

    print(
        "Actual positive fraction:",
        np.round(
            fraction_positive,
            4,
        ),
    )


# =========================================================
# Probability distributions
# =========================================================

print()
print("=" * 80)
print("PROBABILITY SUMMARY")
print("=" * 80)

probability_summary = pd.DataFrame(
    {
        "Uncalibrated": base_probabilities,
        "Sigmoid": sigmoid_probabilities,
        "Isotonic": isotonic_probabilities,
    }
)

print(
    probability_summary.describe().to_string()
)


# =========================================================
# Final comparison table
# =========================================================

print()
print("=" * 80)
print("FINAL COMPARISON")
print("=" * 80)

results_df = pd.DataFrame(results)

print(
    results_df.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}",
    )
)


print()
print("=" * 80)
print("INTERPRETATION")
print("=" * 80)

print(
    """
Lower Brier score generally indicates better
probability calibration.

ROC-AUC and PR-AUC measure ranking/classification
performance and should be considered separately
from calibration.

No production probability interpretation or
risk threshold has been selected.
"""
)