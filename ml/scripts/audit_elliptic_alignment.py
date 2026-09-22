from pathlib import Path

import pandas as pd


FEATURES_PATH = Path(
    "ml/datasets/raw/elliptic_plus_plus/actors/wallets_features.csv"
)

CLASSES_PATH = Path(
    "ml/datasets/raw/elliptic_plus_plus/actors/wallets_classes.csv"
)


def main():
    print("=" * 75)
    print("ELLIPTIC++ WALLET FEATURES / LABEL ALIGNMENT AUDIT")
    print("=" * 75)

    print("\nLoading labels...")
    classes = pd.read_csv(CLASSES_PATH)

    print("Loading features...")
    features = pd.read_csv(FEATURES_PATH)

    print("\n--- BASIC COUNTS ---")
    print(f"Label rows:              {len(classes):,}")
    print(f"Feature rows:            {len(features):,}")
    print(f"Unique labeled addresses:{classes['address'].nunique():,}")
    print(f"Unique feature addresses: {features['address'].nunique():,}")

    label_addresses = set(classes["address"])
    feature_addresses = set(features["address"])

    common_addresses = label_addresses & feature_addresses
    labels_only = label_addresses - feature_addresses
    features_only = feature_addresses - label_addresses

    print("\n--- ADDRESS ALIGNMENT ---")
    print(f"Addresses in both files: {len(common_addresses):,}")
    print(f"Addresses only in labels: {len(labels_only):,}")
    print(f"Addresses only in features: {len(features_only):,}")

    print("\n--- FEATURE ROW LABEL COVERAGE ---")

    features["class"] = features["address"].map(
        classes.set_index("address")["class"]
    )

    print(
        f"Feature rows with labels: "
        f"{features['class'].notna().sum():,}"
    )

    print(
        f"Feature rows without labels: "
        f"{features['class'].isna().sum():,}"
    )

    print("\n--- LABELED FEATURE ROW DISTRIBUTION ---")

    labeled_features = features.dropna(subset=["class"]).copy()
    labeled_features["class"] = labeled_features["class"].astype(int)

    print(
        labeled_features["class"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print("\nPercentages:")

    print(
        (
            labeled_features["class"]
            .value_counts(normalize=True)
            .sort_index()
            * 100
        )
        .round(2)
        .to_string()
    )

    print("\n--- ADDRESS-LEVEL TIME STEP COVERAGE ---")

    timestep_counts = (
        labeled_features.groupby("address")["Time step"]
        .nunique()
    )

    print(f"Addresses with features: {len(timestep_counts):,}")

    print(
        f"Average time steps/address: "
        f"{timestep_counts.mean():.2f}"
    )

    print(
        f"Median time steps/address: "
        f"{timestep_counts.median():.2f}"
    )

    print(
        f"Maximum time steps/address: "
        f"{timestep_counts.max()}"
    )

    print("\nTime-step distribution:")

    print(
        timestep_counts.describe().to_string()
    )

    print("\n--- CLASS BY TIME STEP ---")

    class_by_timestep = pd.crosstab(
        labeled_features["Time step"],
        labeled_features["class"]
    )

    print(class_by_timestep.to_string())

    print("\n--- ADDRESS LABEL CONSISTENCY ---")

    label_counts_per_address = (
        classes.groupby("address")["class"]
        .nunique()
    )

    conflicts = (label_counts_per_address > 1).sum()

    print(f"Addresses with conflicting labels: {conflicts:,}")

    print("\n--- UNKNOWN LABELS ---")

    unknown_rows = (labeled_features["class"] == 1).sum()
    licit_rows = (labeled_features["class"] == 2).sum()
    illicit_rows = (labeled_features["class"] == 3).sum()

    print(f"Unknown feature rows: {unknown_rows:,}")
    print(f"Licit feature rows:   {licit_rows:,}")
    print(f"Illicit feature rows: {illicit_rows:,}")

    print("\n--- BINARY VALIDATION SET ---")

    binary = labeled_features[
        labeled_features["class"].isin([2, 3])
    ]

    print(f"Licit + illicit rows: {len(binary):,}")
    print(f"Unique addresses:     {binary['address'].nunique():,}")

    print("\nBinary class distribution:")

    print(
        binary["class"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print("\nBinary class percentages:")

    print(
        (
            binary["class"]
            .value_counts(normalize=True)
            .sort_index()
            * 100
        )
        .round(2)
        .to_string()
    )

    print("\n--- TIME STEP RANGE ---")
    print(f"Minimum: {features['Time step'].min()}")
    print(f"Maximum: {features['Time step'].max()}")
    print(f"Unique:  {features['Time step'].nunique()}")

    print("\n" + "=" * 75)
    print("ALIGNMENT AUDIT COMPLETE")
    print("=" * 75)


if __name__ == "__main__":
    main()
