from pathlib import Path

import pandas as pd


INPUT_PATH = Path(
    "ml/datasets/processed/elliptic_plus_plus/elliptic_wallet_validation.csv"
)

OUTPUT_DIR = Path("ml/datasets/processed/elliptic_plus_plus")


# Features that describe when the wallet appeared in the dataset/blockchain.
# We keep these separately because they can contain dataset/time-position effects.
TEMPORAL_CONTEXT_FEATURES = {
    "first_block_appeared_in_mean",
    "first_block_appeared_in_max",
    "last_block_appeared_in_mean",
    "last_block_appeared_in_max",
    "first_sent_block_mean",
    "first_sent_block_max",
    "first_received_block_mean",
    "first_received_block_max",
    "time_steps_observed",
    "first_time_step",
    "last_time_step",
}


# Identifier columns must never become model features.
IDENTIFIER_COLUMNS = {
    "address",
    "target",
}


def main() -> None:
    print("=" * 75)
    print("ELLIPTIC++ MODEL FEATURE PREPARATION")
    print("=" * 75)

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input dataset not found: {INPUT_PATH}"
        )

    df = pd.read_csv(INPUT_PATH)

    print("\nInput dataset:")
    print(f"Rows:    {len(df):,}")
    print(f"Columns: {len(df.columns):,}")

    # ------------------------------------------------------------
    # 1. Validate target
    # ------------------------------------------------------------

    if "target" not in df.columns:
        raise ValueError("target column is missing")

    target_values = set(df["target"].dropna().unique())

    if not target_values.issubset({0, 1}):
        raise ValueError(
            f"Unexpected target values: {sorted(target_values)}"
        )

    print("\nTarget distribution:")
    print(df["target"].value_counts().sort_index())

    # ------------------------------------------------------------
    # 2. Identify numeric model candidates
    # ------------------------------------------------------------

    numeric_columns = [
        column
        for column in df.columns
        if column not in IDENTIFIER_COLUMNS
        and pd.api.types.is_numeric_dtype(df[column])
    ]

    # ------------------------------------------------------------
    # 3. Separate temporal-context features
    # ------------------------------------------------------------

    temporal_features = [
        column
        for column in numeric_columns
        if column in TEMPORAL_CONTEXT_FEATURES
    ]

    behavioral_features = [
        column
        for column in numeric_columns
        if column not in TEMPORAL_CONTEXT_FEATURES
    ]

    # Preserve the original column order.
    behavioral_features = [
        column for column in df.columns
        if column in behavioral_features
    ]

    temporal_features = [
        column for column in df.columns
        if column in temporal_features
    ]

    print("\nFeature separation:")
    print(f"Behavioral features:       {len(behavioral_features)}")
    print(f"Temporal-context features: {len(temporal_features)}")

    print("\n--- BEHAVIORAL FEATURES ---")

    for column in behavioral_features:
        print(f"  - {column}")

    print("\n--- TEMPORAL-CONTEXT FEATURES ---")

    for column in temporal_features:
        print(f"  - {column}")

    # ------------------------------------------------------------
    # 4. Create behavioral-only dataset
    # ------------------------------------------------------------

    behavioral_columns = (
        ["address"]
        + behavioral_features
        + ["target"]
    )

    behavioral_df = df[behavioral_columns].copy()

    # ------------------------------------------------------------
    # 5. Create behavioral + temporal dataset
    # ------------------------------------------------------------

    behavioral_temporal_columns = (
        ["address"]
        + behavioral_features
        + temporal_features
        + ["target"]
    )

    behavioral_temporal_df = df[
        behavioral_temporal_columns
    ].copy()

    # ------------------------------------------------------------
    # 6. Validation
    # ------------------------------------------------------------

    print("\nValidation:")

    for name, dataset in [
        ("behavioral", behavioral_df),
        ("behavioral_temporal", behavioral_temporal_df),
    ]:
        feature_columns = [
            column
            for column in dataset.columns
            if column not in {"address", "target"}
        ]

        missing_count = int(dataset.isna().sum().sum())
        duplicate_count = int(dataset.duplicated().sum())

        print(f"\n{name}:")
        print(f"  rows:       {len(dataset):,}")
        print(f"  columns:    {len(dataset.columns):,}")
        print(f"  features:   {len(feature_columns):,}")
        print(f"  missing:    {missing_count:,}")
        print(f"  duplicates: {duplicate_count:,}")

        if "address" in dataset.columns:
            print(
                f"  addresses:  "
                f"{dataset['address'].nunique():,}"
            )

        if missing_count != 0:
            raise ValueError(
                f"{name} dataset contains missing values"
            )

        if duplicate_count != 0:
            raise ValueError(
                f"{name} dataset contains duplicate rows"
            )

    # ------------------------------------------------------------
    # 7. Save datasets
    # ------------------------------------------------------------

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    behavioral_path = (
        OUTPUT_DIR / "elliptic_behavioral.csv"
    )

    behavioral_temporal_path = (
        OUTPUT_DIR / "elliptic_behavioral_temporal.csv"
    )

    behavioral_df.to_csv(
        behavioral_path,
        index=False,
    )

    behavioral_temporal_df.to_csv(
        behavioral_temporal_path,
        index=False,
    )

    # ------------------------------------------------------------
    # 8. Final summary
    # ------------------------------------------------------------

    print("\nSaved datasets:")

    print(f"  Behavioral-only:")
    print(f"    {behavioral_path}")

    print(f"\n  Behavioral + temporal-context:")
    print(f"    {behavioral_temporal_path}")

    print("\nFinal shapes:")
    print(
        f"  Behavioral-only: "
        f"{behavioral_df.shape[0]:,} rows x "
        f"{behavioral_df.shape[1]:,} columns"
    )

    print(
        f"  Behavioral + temporal: "
        f"{behavioral_temporal_df.shape[0]:,} rows x "
        f"{behavioral_temporal_df.shape[1]:,} columns"
    )

    print("\n" + "=" * 75)
    print("FEATURE PREPARATION COMPLETE")
    print("=" * 75)


if __name__ == "__main__":
    main()