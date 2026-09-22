from pathlib import Path

import numpy as np
import pandas as pd


# =========================================================
# Paths
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = (
    PROJECT_ROOT
    / "ml"
    / "datasets"
    / "processed"
    / "ethereum_fraud"
    / "ethereum_fraud_clean.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "ml"
    / "datasets"
    / "processed"
    / "ethereum_fraud"
    / "ethereum_fraud_features.csv"
)


# =========================================================
# Load
# =========================================================

df = pd.read_csv(INPUT_PATH)

print("Original shape:", df.shape)


# =========================================================
# Helper functions
# =========================================================

def safe_divide(
    numerator: pd.Series,
    denominator: pd.Series,
) -> pd.Series:
    """
    Safely divide two pandas Series.

    Zero denominators become zero.
    Infinite values become zero.
    """

    result = numerator / denominator.replace(
        0,
        np.nan,
    )

    return (
        result
        .replace(
            [np.inf, -np.inf],
            np.nan,
        )
        .fillna(0)
    )


def find_column(
    exact_name: str,
) -> str:
    """
    Find a column while ignoring capitalization
    and surrounding whitespace.

    This prevents errors caused by inconsistent
    capitalization in the source dataset.
    """

    normalized_target = (
        exact_name
        .strip()
        .lower()
    )

    for column in df.columns:
        normalized_column = (
            column
            .strip()
            .lower()
        )

        if normalized_column == normalized_target:
            return column

    raise KeyError(
        f"Required column not found: {exact_name}"
    )


# =========================================================
# Resolve source columns
# =========================================================

COL = {
    "total_transactions": find_column(
        "total transactions (including tnx to create contract"
    ),
    "sent_tnx": find_column(
        "Sent tnx"
    ),
    "received_tnx": find_column(
        "Received Tnx"
    ),
    "unique_received": find_column(
        "Unique Received From Addresses"
    ),
    "unique_sent": find_column(
        "Unique Sent To Addresses"
    ),
    "total_sent": find_column(
        "total Ether sent"
    ),
    "total_received": find_column(
        "total ether received"
    ),
    "total_sent_contracts": find_column(
        "total ether sent contracts"
    ),
    "created_contracts": find_column(
        "Number of Created Contracts"
    ),
    "activity_minutes": find_column(
        "Time Diff between first and last (Mins)"
    ),
    "erc20_transactions": find_column(
        "Total ERC20 tnxs"
    ),
    "erc20_sent": find_column(
        "ERC20 total ether sent"
    ),
    "erc20_received": find_column(
        "ERC20 total Ether received"
    ),
    "erc20_sent_addresses": find_column(
        "ERC20 uniq sent addr"
    ),
    "erc20_received_addresses": find_column(
        "ERC20 uniq rec addr"
    ),
}


print()
print("Resolved source columns:")

for name, column in COL.items():
    print(f"{name}: {column}")


# =========================================================
# Transaction activity
# =========================================================

df["transaction_velocity"] = safe_divide(
    df[COL["total_transactions"]],
    df[COL["activity_minutes"]],
)

df["sent_transaction_ratio"] = safe_divide(
    df[COL["sent_tnx"]],
    df[COL["total_transactions"]],
)

df["received_transaction_ratio"] = safe_divide(
    df[COL["received_tnx"]],
    df[COL["total_transactions"]],
)


# =========================================================
# Counterparty behavior
# =========================================================

df["incoming_counterparty_density"] = safe_divide(
    df[COL["unique_received"]],
    df[COL["received_tnx"]],
)

df["outgoing_counterparty_density"] = safe_divide(
    df[COL["unique_sent"]],
    df[COL["sent_tnx"]],
)


# =========================================================
# Value flow
# =========================================================

df["average_total_value"] = safe_divide(
    df[COL["total_sent"]]
    + df[COL["total_received"]],
    df[COL["total_transactions"]],
)

df["average_sent_value"] = safe_divide(
    df[COL["total_sent"]],
    df[COL["sent_tnx"]],
)

df["average_received_value"] = safe_divide(
    df[COL["total_received"]],
    df[COL["received_tnx"]],
)

df["outgoing_incoming_value_ratio"] = safe_divide(
    df[COL["total_sent"]],
    df[COL["total_received"]],
)


# =========================================================
# Contract behavior
# =========================================================

df["contract_transaction_ratio"] = safe_divide(
    df[COL["total_sent_contracts"]],
    df[COL["total_sent"]],
)

df["created_contract_ratio"] = safe_divide(
    df[COL["created_contracts"]],
    df[COL["total_transactions"]],
)


# =========================================================
# ERC20 behavior
# =========================================================

df["erc20_transaction_ratio"] = safe_divide(
    df[COL["erc20_transactions"]],
    df[COL["total_transactions"]],
)

df["erc20_incoming_outgoing_ratio"] = safe_divide(
    df[COL["erc20_sent"]],
    df[COL["erc20_received"]],
)

df["erc20_sent_counterparty_density"] = safe_divide(
    df[COL["erc20_sent_addresses"]],
    df[COL["erc20_transactions"]],
)

df["erc20_received_counterparty_density"] = safe_divide(
    df[COL["erc20_received_addresses"]],
    df[COL["erc20_transactions"]],
)


# =========================================================
# Activity intensity
# =========================================================

df["activity_hours"] = (
    df[COL["activity_minutes"]]
    / 60.0
)

df["transactions_per_hour"] = safe_divide(
    df[COL["total_transactions"]],
    df["activity_hours"],
)


# =========================================================
# Clean generated values
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


# =========================================================
# Summary
# =========================================================

NEW_FEATURES = [
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


print()
print("========================================")
print("FEATURE ENGINEERING COMPLETE")
print("========================================")

print("Output:", OUTPUT_PATH)
print("Final shape:", df.shape)

print()
print("New features:")

for feature in NEW_FEATURES:
    print("-", feature)

print()
print("Missing values:", df.isna().sum().sum())