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

OUTPUT_PATH = (
    PROJECT_ROOT
    / "ml"
    / "datasets"
    / "processed"
    / "ethereum_fraud"
    / "ethereum_fraud_model_ready.csv"
)


df = pd.read_csv(INPUT_PATH)

print("Input shape:", df.shape)


# =========================================================
# Log-transform heavy-tailed ratios
# =========================================================

df["log_outgoing_incoming_value_ratio"] = np.log1p(
    df["outgoing_incoming_value_ratio"]
)

df["log_erc20_incoming_outgoing_ratio"] = np.log1p(
    df["erc20_incoming_outgoing_ratio"]
)


# =========================================================
# Remove redundant / unsuitable engineered features
# =========================================================

REMOVE_COLUMNS = [
    "transaction_velocity",
    "transactions_per_hour",
    "received_transaction_ratio",
    "contract_transaction_ratio",
    "outgoing_incoming_value_ratio",
    "erc20_incoming_outgoing_ratio",
]

df = df.drop(
    columns=REMOVE_COLUMNS,
    errors="ignore",
)


# =========================================================
# Clean numeric values
# =========================================================

numeric_columns = df.select_dtypes(
    include=["number"]
).columns

df[numeric_columns] = (
    df[numeric_columns]
    .replace(
        [np.inf, -np.inf],
        np.nan,
    )
    .fillna(0)
)


# =========================================================
# Save
# =========================================================

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)

df.to_csv(
    OUTPUT_PATH,
    index=False,
)


print()
print("=" * 80)
print("MODEL FEATURE PREPARATION COMPLETE")
print("=" * 80)

print("Output:", OUTPUT_PATH)
print("Final shape:", df.shape)

print()
print("Removed:")
for column in REMOVE_COLUMNS:
    print("-", column)

print()
print("Added:")
print("- log_outgoing_incoming_value_ratio")
print("- log_erc20_incoming_outgoing_ratio")

print()
print("Missing values:", df.isna().sum().sum())

print()
print("Target distribution:")
print(df["FLAG"].value_counts().sort_index())