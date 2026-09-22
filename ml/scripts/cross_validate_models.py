from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = (
    PROJECT_ROOT
    / "ml"
    / "datasets"
    / "processed"
    / "ethereum_fraud"
    / "ethereum_fraud_model_ready.csv"
)


# =========================================================
# Load
# =========================================================

df = pd.read_csv(INPUT_PATH)

TARGET = "FLAG"

TOKEN_COLUMNS = [
    "ERC20 most sent token type",
    "ERC20_most_rec_token_type",
]

X = df.drop(
    columns=[TARGET] + TOKEN_COLUMNS,
    errors="ignore",
)

y = df[TARGET]

# Numeric behavioral features only
X = X.select_dtypes(
    include=["number"]
)


print("=" * 80)
print("5-FOLD CROSS-VALIDATION")
print("=" * 80)

print()
print("Dataset:", df.shape)
print("Features:", X.shape[1])
print("Samples:", len(X))

print()
print("Class distribution:")
print(y.value_counts().sort_index())


# =========================================================
# Define the two feature sets
# =========================================================

ENGINEERED_FEATURES = [
    "sent_transaction_ratio",
    "incoming_counterparty_density",
    "outgoing_counterparty_density",
    "average_total_value",
    "average_sent_value",
    "average_received_value",
    "created_contract_ratio",
    "erc20_transaction_ratio",
    "erc20_sent_counterparty_density",
    "erc20_received_counterparty_density",
    "activity_hours",
    "log_outgoing_incoming_value_ratio",
    "log_erc20_incoming_outgoing_ratio",
]


# Original behavioral features are everything except
# the engineered features.
BASELINE_FEATURES = [
    column
    for column in X.columns
    if column not in ENGINEERED_FEATURES
]


ENGINEERED_MODEL_FEATURES = [
    column
    for column in X.columns
]


print()
print("Baseline behavioral features:", len(BASELINE_FEATURES))
print("Engineered behavioral features:", len(ENGINEERED_MODEL_FEATURES))


# =========================================================
# Cross-validation configuration
# =========================================================

cv = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42,
)


# =========================================================
# Evaluation function
# =========================================================

def evaluate_feature_set(
    feature_columns,
    model_name,
):
    results = []

    print()
    print("=" * 80)
    print(model_name)
    print("=" * 80)

    for fold, (train_index, test_index) in enumerate(
        cv.split(X, y),
        start=1,
    ):
        X_train = X.iloc[
            train_index
        ][feature_columns]

        X_test = X.iloc[
            test_index
        ][feature_columns]

        y_train = y.iloc[
            train_index
        ]

        y_test = y.iloc[
            test_index
        ]

        model = RandomForestClassifier(
            n_estimators=300,
            random_state=42,
            n_jobs=-1,
            class_weight="balanced",
        )

        model.fit(
            X_train,
            y_train,
        )

        predictions = model.predict(
            X_test
        )

        probabilities = model.predict_proba(
            X_test
        )[:, 1]

        precision = precision_score(
            y_test,
            predictions,
            pos_label=1,
            zero_division=0,
        )

        recall = recall_score(
            y_test,
            predictions,
            pos_label=1,
            zero_division=0,
        )

        f1 = f1_score(
            y_test,
            predictions,
            pos_label=1,
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

        results.append(
            {
                "fold": fold,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "roc_auc": roc_auc,
                "pr_auc": pr_auc,
            }
        )

        print(
            f"Fold {fold}: "
            f"Precision={precision:.4f} | "
            f"Recall={recall:.4f} | "
            f"F1={f1:.4f} | "
            f"ROC-AUC={roc_auc:.4f} | "
            f"PR-AUC={pr_auc:.4f}"
        )

    results_df = pd.DataFrame(results)

    print()
    print("Mean ± Standard Deviation")

    for metric in [
        "precision",
        "recall",
        "f1",
        "roc_auc",
        "pr_auc",
    ]:
        mean = results_df[metric].mean()
        std = results_df[metric].std()

        print(
            f"{metric:10s}: "
            f"{mean:.4f} ± {std:.4f}"
        )

    return results_df


# =========================================================
# Run both experiments
# =========================================================

baseline_results = evaluate_feature_set(
    BASELINE_FEATURES,
    "MODEL A — BASELINE BEHAVIORAL",
)

engineered_results = evaluate_feature_set(
    ENGINEERED_MODEL_FEATURES,
    "MODEL B — ENGINEERED BEHAVIORAL",
)


# =========================================================
# Final comparison
# =========================================================

print()
print("=" * 80)
print("FINAL CROSS-VALIDATION COMPARISON")
print("=" * 80)

comparison_rows = []

for metric in [
    "precision",
    "recall",
    "f1",
    "roc_auc",
    "pr_auc",
]:

    baseline_mean = baseline_results[
        metric
    ].mean()

    engineered_mean = engineered_results[
        metric
    ].mean()

    difference = (
        engineered_mean
        - baseline_mean
    )

    comparison_rows.append(
        {
            "metric": metric,
            "baseline_mean": baseline_mean,
            "engineered_mean": engineered_mean,
            "difference": difference,
        }
    )


comparison = pd.DataFrame(
    comparison_rows
)

print(
    comparison.to_string(
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
This experiment compares the models using the same
5 stratified folds.

Positive difference means the engineered feature set
performed better on that metric.

This is an evaluation experiment, not a production
risk determination.
"""
)