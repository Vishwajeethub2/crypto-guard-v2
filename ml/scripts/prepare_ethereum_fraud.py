from pathlib import Path

import pandas as pd


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_PATH = (
    PROJECT_ROOT
    / "ml"
    / "datasets"
    / "raw"
    / "ethereum_fraud"
    / "transaction_dataset.csv"
)

PROCESSED_DIR = (
    PROJECT_ROOT
    / "ml"
    / "datasets"
    / "processed"
    / "ethereum_fraud"
)

OUTPUT_PATH = PROCESSED_DIR / "ethereum_fraud_clean.csv"


# ---------------------------------------------------------
# Load raw dataset
# ---------------------------------------------------------

print("Loading raw dataset...")
df = pd.read_csv(RAW_PATH)

print(f"Original shape: {df.shape}")


# ---------------------------------------------------------
# Remove dataset/index identifiers
# ---------------------------------------------------------

DROP_COLUMNS = [
    "Unnamed: 0",
    "Index",
    "Address",
]

existing_drop_columns = [
    column for column in DROP_COLUMNS
    if column in df.columns
]

df = df.drop(columns=existing_drop_columns)

print(f"Removed columns: {existing_drop_columns}")


# ---------------------------------------------------------
# Normalize column names
# ---------------------------------------------------------

df.columns = (
    df.columns
    .str.strip()
    .str.replace(r"\s+", " ", regex=True)
)


# ---------------------------------------------------------
# Handle categorical token columns
# ---------------------------------------------------------

CATEGORICAL_COLUMNS = [
    "ERC20 most sent token type",
    "ERC20_most_rec_token_type",
]

for column in CATEGORICAL_COLUMNS:
    if column in df.columns:
        df[column] = df[column].fillna("UNKNOWN")


# ---------------------------------------------------------
# Handle numeric missing values
# ---------------------------------------------------------

numeric_columns = df.select_dtypes(
    include=["number"]
).columns.tolist()

numeric_feature_columns = [
    column for column in numeric_columns
    if column != "FLAG"
]

for column in numeric_feature_columns:
    df[column] = df[column].fillna(0)


# ---------------------------------------------------------
# Validate target
# ---------------------------------------------------------

if "FLAG" not in df.columns:
    raise ValueError("FLAG target column was not found.")

if not set(df["FLAG"].dropna().unique()).issubset({0, 1}):
    raise ValueError("FLAG contains unexpected target values.")


# ---------------------------------------------------------
# Remove rows with missing target
# ---------------------------------------------------------

before_target_cleanup = len(df)

df = df.dropna(subset=["FLAG"])

after_target_cleanup = len(df)

print(
    "Rows removed because of missing FLAG:",
    before_target_cleanup - after_target_cleanup,
)


# ---------------------------------------------------------
# Remove duplicate rows after cleaning
# ---------------------------------------------------------

before_duplicates = len(df)

df = df.drop_duplicates()

after_duplicates = len(df)

print(
    "Duplicate rows removed:",
    before_duplicates - after_duplicates,
)


# ---------------------------------------------------------
# Ensure target is integer
# ---------------------------------------------------------

df["FLAG"] = df["FLAG"].astype(int)


# ---------------------------------------------------------
# Create output directory
# ---------------------------------------------------------

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ---------------------------------------------------------
# Save processed dataset
# ---------------------------------------------------------

df.to_csv(
    OUTPUT_PATH,
    index=False,
)


# ---------------------------------------------------------
# Final summary
# ---------------------------------------------------------

print()
print("========================================")
print("Dataset preparation complete")
print("========================================")
print(f"Output: {OUTPUT_PATH}")
print(f"Final shape: {df.shape}")
print()
print("Class distribution:")
print(df["FLAG"].value_counts().to_string())
print()
print("Missing values remaining:")
print(df.isna().sum().sum())
print()
print("Columns:")
print(df.columns.tolist())