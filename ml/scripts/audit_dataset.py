from pathlib import Path

import pandas as pd


# =========================================================
# Paths
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_PATH = (
    PROJECT_ROOT
    / "ml"
    / "datasets"
    / "raw"
    / "ethereum_fraud"
    / "transaction_dataset.csv"
)


# =========================================================
# Load
# =========================================================

df = pd.read_csv(RAW_PATH)

print("=" * 60)
print("CRYPTO GUARD - DATASET AUDIT")
print("=" * 60)

print("\nShape:")
print(df.shape)


# =========================================================
# Target
# =========================================================

print("\nFLAG distribution:")
print(df["FLAG"].value_counts().to_string())

print("\nFLAG percentage:")
print(
    (df["FLAG"].value_counts(normalize=True) * 100)
    .round(2)
    .to_string()
)


# =========================================================
# Address structure
# =========================================================

address_counts = df["Address"].value_counts()

print("\nAddress statistics:")
print("Rows:", len(df))
print("Unique addresses:", df["Address"].nunique())
print("Repeated addresses:", (address_counts > 1).sum())
print("Maximum rows for one address:", address_counts.max())


# =========================================================
# Duplicate addresses and labels
# =========================================================

address_label_counts = (
    df.groupby("Address")["FLAG"]
    .nunique()
)

conflicting_addresses = address_label_counts[
    address_label_counts > 1
]

print("\nAddresses with conflicting FLAG labels:")
print(len(conflicting_addresses))


# =========================================================
# Index structure
# =========================================================

print("\nIndex statistics:")
print("Minimum:", df["Index"].min())
print("Maximum:", df["Index"].max())
print("Unique:", df["Index"].nunique())


# =========================================================
# FLAG rate by Index quartile
# =========================================================

df["IndexQuartile"] = pd.qcut(
    df["Index"],
    4,
    duplicates="drop",
)

index_distribution = pd.crosstab(
    df["IndexQuartile"],
    df["FLAG"],
    normalize="index",
).round(4)

print("\nFLAG distribution by Index quartile:")
print(index_distribution.to_string())


# =========================================================
# Check whether rows are grouped by address
# =========================================================

address_changes = (
    df["Address"] != df["Address"].shift()
).sum()

print("\nAddress ordering:")
print(
    "Number of address changes between consecutive rows:",
    address_changes,
)


# =========================================================
# Check for timestamp-like columns
# =========================================================

timestamp_candidates = [
    column
    for column in df.columns
    if any(
        word in column.lower()
        for word in [
            "time",
            "date",
            "timestamp",
            "block",
        ]
    )
]

print("\nTimestamp/block-like columns:")
print(timestamp_candidates)


# =========================================================
# Check raw duplicate rows
# =========================================================

print("\nExact duplicate rows:")
print(df.duplicated().sum())


# =========================================================
# Summary
# =========================================================

print("\n" + "=" * 60)
print("AUDIT COMPLETE")
print("=" * 60)