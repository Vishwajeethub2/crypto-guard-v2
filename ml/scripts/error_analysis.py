from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
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


# =========================================================
# Configuration
# =========================================================

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
print("MODEL ERROR ANALYSIS")
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
# Train / test split
# =========================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=RANDOM_STATE,
    stratify=y,
)


print()
print("Training rows:", len(X_train))
print("Testing rows :", len(X_test))


# =========================================================
# Train engineered behavioral model
# =========================================================

model = RandomForestClassifier(
    n_estimators=300,
    random_state=RANDOM_STATE,
    n_jobs=-1,
    class_weight="balanced",
)

print()
print("Training Random Forest...")

model.fit(
    X_train,
    y_train,
)


# =========================================================
# Predictions
# =========================================================

probabilities = model.predict_proba(
    X_test
)[:, 1]

predictions = (
    probabilities >= 0.50
).astype(int)


# =========================================================
# Basic metrics
# =========================================================

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


print()
print("=" * 80)
print("BASELINE TEST-SET RESULTS")
print("=" * 80)

print(f"Precision : {precision:.4f}")
print(f"Recall    : {recall:.4f}")
print(f"F1        : {f1:.4f}")
print(f"ROC-AUC   : {roc_auc:.4f}")
print(f"PR-AUC    : {pr_auc:.4f}")

print()
print("Confusion Matrix:")
print(confusion_matrix(y_test, predictions))


# =========================================================
# Build analysis dataframe
# =========================================================

analysis = X_test.copy()

analysis["actual"] = y_test.values
analysis["predicted"] = predictions
analysis["probability"] = probabilities

analysis["error_type"] = "correct"

analysis.loc[
    (analysis["actual"] == 1)
    & (analysis["predicted"] == 0),
    "error_type",
] = "false_negative"

analysis.loc[
    (analysis["actual"] == 0)
    & (analysis["predicted"] == 1),
    "error_type",
] = "false_positive"


# =========================================================
# Error counts
# =========================================================

false_positive_count = (
    analysis["error_type"]
    .eq("false_positive")
    .sum()
)

false_negative_count = (
    analysis["error_type"]
    .eq("false_negative")
    .sum()
)

print()
print("=" * 80)
print("ERROR COUNTS")
print("=" * 80)

print(
    "False positives:",
    false_positive_count,
)

print(
    "False negatives:",
    false_negative_count,
)


# =========================================================
# False negatives
# =========================================================

false_negatives = analysis[
    analysis["error_type"]
    == "false_negative"
].copy()

print()
print("=" * 80)
print("FALSE NEGATIVES")
print("=" * 80)

print(
    "These are labeled fraud cases that the model predicted as normal."
)

if len(false_negatives) > 0:

    print()
    print(
        "Probability statistics:"
    )

    print(
        false_negatives[
            "probability"
        ].describe().to_string()
    )

    print()
    print(
        "Highest-probability false negatives:"
    )

    print(
        false_negatives
        .sort_values(
            "probability",
            ascending=False,
        )
        .head(15)
        .to_string()
    )

else:
    print("No false negatives.")


# =========================================================
# False positives
# =========================================================

false_positives = analysis[
    analysis["error_type"]
    == "false_positive"
].copy()

print()
print("=" * 80)
print("FALSE POSITIVES")
print("=" * 80)

print(
    "These are labeled normal cases that the model predicted as fraud."
)

if len(false_positives) > 0:

    print()
    print(
        "Probability statistics:"
    )

    print(
        false_positives[
            "probability"
        ].describe().to_string()
    )

    print()
    print(
        "Highest-probability false positives:"
    )

    print(
        false_positives
        .sort_values(
            "probability",
            ascending=False,
        )
        .head(15)
        .to_string()
    )

else:
    print("No false positives.")


# =========================================================
# Threshold analysis
# =========================================================

print()
print("=" * 80)
print("THRESHOLD ANALYSIS")
print("=" * 80)

thresholds = [
    0.20,
    0.30,
    0.40,
    0.50,
    0.60,
    0.70,
    0.80,
    0.90,
]

threshold_results = []

for threshold in thresholds:

    threshold_predictions = (
        probabilities >= threshold
    ).astype(int)

    threshold_precision = precision_score(
        y_test,
        threshold_predictions,
        zero_division=0,
    )

    threshold_recall = recall_score(
        y_test,
        threshold_predictions,
        zero_division=0,
    )

    threshold_f1 = f1_score(
        y_test,
        threshold_predictions,
        zero_division=0,
    )

    matrix = confusion_matrix(
        y_test,
        threshold_predictions,
    )

    tn, fp, fn, tp = matrix.ravel()

    threshold_results.append(
        {
            "threshold": threshold,
            "precision": threshold_precision,
            "recall": threshold_recall,
            "f1": threshold_f1,
            "false_positives": fp,
            "false_negatives": fn,
            "true_positives": tp,
            "true_negatives": tn,
        }
    )


threshold_df = pd.DataFrame(
    threshold_results
)

print(
    threshold_df.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}",
    )
)


# =========================================================
# Probability distribution
# =========================================================

print()
print("=" * 80)
print("PROBABILITY DISTRIBUTION")
print("=" * 80)

print()
print("Actual normal wallets:")
print(
    pd.Series(
        probabilities[
            y_test.values == 0
        ]
    ).describe().to_string()
)

print()
print("Actual fraud wallets:")
print(
    pd.Series(
        probabilities[
            y_test.values == 1
        ]
    ).describe().to_string()
)


# =========================================================
# Top feature importance
# =========================================================

feature_importance = (
    pd.DataFrame(
        {
            "feature": X.columns,
            "importance": model.feature_importances_,
        }
    )
    .sort_values(
        "importance",
        ascending=False,
    )
)

print()
print("=" * 80)
print("TOP 20 FEATURES")
print("=" * 80)

print(
    feature_importance
    .head(20)
    .to_string(
        index=False
    )
)


# =========================================================
# Final message
# =========================================================

print()
print("=" * 80)
print("ERROR ANALYSIS COMPLETE")
print("=" * 80)

print(
    """
This experiment is diagnostic.

The threshold table shows how changing the
classification threshold changes precision,
recall and false-positive / false-negative counts.

No production threshold has been selected.
"""
)