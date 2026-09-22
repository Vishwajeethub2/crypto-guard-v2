from pathlib import Path

import pandas as pd


FEATURES_PATH = Path(
    "ml/datasets/raw/elliptic_plus_plus/actors/wallets_features.csv"
)

CLASSES_PATH = Path(
    "ml/datasets/raw/elliptic_plus_plus/actors/wallets_classes.csv"
)

OUTPUT_DIR = Path(
    "ml/datasets/processed/elliptic_plus_plus"
)

OUTPUT_PATH = OUTPUT_DIR / "elliptic_wallet_validation.csv"


def main():
    print("=" * 75)
    print("BUILD ELLIPTIC++ WALLET-LEVEL VALIDATION DATASET")
    print("=" * 75)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\nLoading labels...")
    labels = pd.read_csv(CLASSES_PATH)

    print("Loading features...")
    features = pd.read_csv(FEATURES_PATH)

    print(f"Feature rows: {len(features):,}")

    # Attach wallet labels.
    features["class"] = features["address"].map(
        labels.set_index("address")["class"]
    )

    # Keep only known licit/illicit wallets.
    features = features[features["class"].isin([2, 3])].copy()

    print(
        f"Known licit/illicit observations: "
        f"{len(features):,}"
    )

    # Convert class:
    # 2 = licit -> 0
    # 3 = illicit -> 1
    features["target"] = (features["class"] == 3).astype("int8")

    # Columns that should NOT be blindly averaged.
    identifier_columns = [
        "address",
        "Time step",
        "class",
        "target",
    ]

    numeric_columns = [
        column
        for column in features.select_dtypes(include="number").columns
        if column not in identifier_columns
    ]

    print(f"\nNumeric behavioral features: {len(numeric_columns)}")

    # Aggregate temporal observations to one row per wallet.
    #
    # For each numeric feature we keep:
    #   mean = typical behavior
    #   max  = peak behavior
    #
    # This preserves more information than taking only a simple mean.
    print("\nAggregating temporal observations by wallet...")

    aggregated = (
        features.groupby("address")[numeric_columns]
        .agg(["mean", "max"])
    )

    # Flatten MultiIndex column names.
    aggregated.columns = [
        f"{column}_{stat}"
        for column, stat in aggregated.columns
    ]

    # Add temporal coverage information.
    temporal = (
        features.groupby("address")
        .agg(
            time_steps_observed=("Time step", "nunique"),
            first_time_step=("Time step", "min"),
            last_time_step=("Time step", "max"),
        )
    )

    # Add the wallet-level target.
    targets = (
        features.groupby("address")["target"]
        .first()
        .astype("int8")
        .rename("target")
    )

    result = pd.concat(
        [
            aggregated,
            temporal,
            targets,
        ],
        axis=1,
    ).reset_index()

    print("\nFinal dataset:")
    print(f"Rows:    {len(result):,}")
    print(f"Columns: {len(result.columns):,}")

    print("\nTarget distribution:")
    print(result["target"].value_counts().sort_index())

    print("\nTarget percentages:")
    print(
        (
            result["target"]
            .value_counts(normalize=True)
            .sort_index()
            * 100
        ).round(2)
    )

    print("\nMissing values:")
    print(result.isna().sum().sum())

    print("\nDuplicate rows:")
    print(result.duplicated().sum())

    print("\nUnique wallets:")
    print(result["address"].nunique())

    result.to_csv(OUTPUT_PATH, index=False)

    print(f"\nSaved to:")
    print(OUTPUT_PATH)

    print("\n" + "=" * 75)
    print("WALLET-LEVEL DATASET CREATED")
    print("=" * 75)


if __name__ == "__main__":
    main()
