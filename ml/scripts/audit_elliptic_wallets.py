from pathlib import Path

import pandas as pd


DATA_PATH = Path(
    "ml/datasets/raw/elliptic_plus_plus/actors/wallets_classes.csv"
)


def main():
    print("=" * 70)
    print("ELLIPTIC++ WALLETS CLASSES AUDIT")
    print("=" * 70)

    df = pd.read_csv(DATA_PATH)

    print(f"\nShape: {df.shape}")

    print("\nColumns:")
    for column in df.columns:
        print(f"  - {column}")

    print("\nFirst 5 rows:")
    print(df.head().to_string(index=False))

    print("\nData types:")
    print(df.dtypes)

    print("\nMissing values:")
    print(df.isna().sum())

    print("\nClass distribution:")
    print(df["class"].value_counts(dropna=False).sort_index())

    print("\nClass percentages:")
    print(
        (df["class"].value_counts(normalize=True, dropna=False) * 100)
        .sort_index()
        .round(2)
    )

    print("\nUnique wallet addresses:")
    print(df["address"].nunique())

    print("\nDuplicate rows:")
    print(df.duplicated().sum())

    print("\nDuplicate addresses:")
    print(df["address"].duplicated().sum())

    print("\nAddress class conflicts:")
    conflicts = (
        df.groupby("address")["class"]
        .nunique()
        .gt(1)
        .sum()
    )
    print(conflicts)

    print("\nUnique class values:")
    print(sorted(df["class"].dropna().unique().tolist()))

    print("\nClass meaning:")
    print("  1 = unknown")
    print("  2 = licit")
    print("  3 = illicit")

    print("\n" + "=" * 70)
    print("AUDIT COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()