from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = (
    PROJECT_ROOT
    / "ml"
    / "datasets"
    / "processed"
    / "ethereum_fraud"
    / "ethereum_fraud_features.csv"
)

df = pd.read_csv(INPUT_PATH)

TARGET = "FLAG"

ENGINEERED_FEATURES = [
    "transaction_velocity",
    "sent_transaction_ratio",
    "received_transaction_ratio",
    "incoming_counterparty_density",
    "outgoing_counterparty_density",
    "average_total_value",
    "average_sent_value",
    "average_received_value",
    "outgoing_incoming_value_ratio",
    "contract_transaction_ratio",
    "created_contract_ratio",
    "erc20_transaction_ratio",
    "erc20_incoming_outgoing_ratio",
    "erc20_sent_counterparty_density",
    "erc20_received_counterparty_density",
    "activity_hours",
    "transactions_per_hour",
]


print("=" * 80)
print("ENGINEERED FEATURE AUDIT")
print("=" * 80)

print()
print("Dataset shape:", df.shape)
print("Target distribution:")
print(df[TARGET].value_counts().sort_index())


# =========================================================
# Distribution audit
# =========================================================

print()
print("=" * 80)
print("1. FEATURE DISTRIBUTIONS")
print("=" * 80)

rows = []

for feature in ENGINEERED_FEATURES:
    series = pd.to_numeric(
        df[feature],
        errors="coerce",
    )

    q99 = series.quantile(0.99)
    q999 = series.quantile(0.999)

    extreme_99 = (series > q99).sum()

    if q99 != 0:
        extreme_ratio = extreme_99 / len(series)
    else:
        extreme_ratio = 0

    rows.append(
        {
            "feature": feature,
            "min": series.min(),
            "median": series.median(),
            "mean": series.mean(),
            "p99": q99,
            "p99_9": q999,
            "max": series.max(),
            "values_above_p99": extreme_99,
            "pct_above_p99": extreme_ratio * 100,
        }
    )

distribution = pd.DataFrame(rows)

print(
    distribution.to_string(
        index=False,
        float_format=lambda x: f"{x:.6g}",
    )
)


# =========================================================
# FLAG relationship
# =========================================================

print()
print("=" * 80)
print("2. RELATIONSHIP WITH FLAG")
print("=" * 80)

for feature in ENGINEERED_FEATURES:
    fraud_mean = df.loc[
        df[TARGET] == 1,
        feature,
    ].mean()

    normal_mean = df.loc[
        df[TARGET] == 0,
        feature,
    ].mean()

    fraud_median = df.loc[
        df[TARGET] == 1,
        feature,
    ].median()

    normal_median = df.loc[
        df[TARGET] == 0,
        feature,
    ].median()

    print()
    print(feature)
    print(f"  normal mean   : {normal_mean:.6g}")
    print(f"  fraud mean    : {fraud_mean:.6g}")
    print(f"  normal median : {normal_median:.6g}")
    print(f"  fraud median  : {fraud_median:.6g}")


# =========================================================
# Correlation with target
# =========================================================

print()
print("=" * 80)
print("3. CORRELATION WITH FLAG")
print("=" * 80)

numeric_df = df[
    ENGINEERED_FEATURES + [TARGET]
].copy()

correlations = (
    numeric_df
    .corr(numeric_only=True)[TARGET]
    .drop(TARGET)
    .sort_values(
        key=lambda x: x.abs(),
        ascending=False,
    )
)

print(correlations.to_string())


# =========================================================
# Duplicate / redundant engineered features
# =========================================================

print()
print("=" * 80)
print("4. ENGINEERED FEATURE CORRELATIONS")
print("=" * 80)

feature_corr = (
    df[ENGINEERED_FEATURES]
    .corr()
    .abs()
)

pairs = []

for i in range(len(ENGINEERED_FEATURES)):
    for j in range(i + 1, len(ENGINEERED_FEATURES)):

        feature_a = ENGINEERED_FEATURES[i]
        feature_b = ENGINEERED_FEATURES[j]

        correlation = feature_corr.loc[
            feature_a,
            feature_b,
        ]

        if correlation >= 0.95:
            pairs.append(
                {
                    "feature_a": feature_a,
                    "feature_b": feature_b,
                    "absolute_correlation": correlation,
                }
            )

if pairs:
    redundant = pd.DataFrame(pairs).sort_values(
        "absolute_correlation",
        ascending=False,
    )

    print(redundant.to_string(index=False))
else:
    print("No feature pairs with absolute correlation >= 0.95.")


# =========================================================
# Zero-heavy features
# =========================================================

print()
print("=" * 80)
print("5. ZERO-VALUE ANALYSIS")
print("=" * 80)

for feature in ENGINEERED_FEATURES:

    zero_count = (
        df[feature] == 0
    ).sum()

    zero_pct = (
        zero_count / len(df)
    ) * 100

    print(
        f"{feature:40s} "
        f"{zero_count:5d} zeros "
        f"({zero_pct:6.2f}%)"
    )


# =========================================================
# Final
# =========================================================

print()
print("=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)

print(
    """
No data was modified.

The purpose of this audit is to decide:
- which ratios need log transformation,
- which features should be retained,
- which redundant features should be removed,
- and which features should be compared in the next ML experiment.
"""
)