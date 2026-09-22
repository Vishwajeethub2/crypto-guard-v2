from pathlib import Path

import pandas as pd


DATA_PATH = Path(
    "ml/datasets/raw/elliptic_plus_plus/actors/wallets_features.csv"
)


def main():
    print("=" * 70)
    print("ELLIPTIC++ WALLETS FEATURES AUDIT")
    print("=" * 70)

    df = pd.read_csv(DATA_PATH)

    print(f"\nShape: {df.shape}")

    print("\nColumns:")
    for i, column in enumerate(df.columns, start=1):
        print(f"  {i:>3}. {column}")

    print("\nData types:")
    print(df.dtypes)

    print("\nFirst 5 rows:")
    print(df.head().to_string(index=False))

    print("\nMissing values:")
    missing = df.isna().sum()
    print(missing[missing > 0].sort_values(ascending=False))

    print("\nTotal missing values:")
    print(df.isna().sum().sum())

    print("\nDuplicate rows:")
    print(df.duplicated().sum())

    print("\nUnique values per column:")
    for column in df.columns:
        print(f"  {column}: {df[column].nunique(dropna=False)}")

    print("\nNumeric columns:")
    numeric_columns = df.select_dtypes(include="number").columns.tolist()
    for column in numeric_columns:
        print(f"  - {column}")

    print(f"\nNumber of numeric columns: {len(numeric_columns)}")

    print("\nNon-numeric columns:")
    non_numeric_columns = df.select_dtypes(exclude="number").columns.tolist()
    for column in non_numeric_columns:
        print(f"  - {column}")

    print(f"\nNumber of non-numeric columns: {len(non_numeric_columns)}")

    print("\nNumeric summary:")
    if numeric_columns:
        print(
            df[numeric_columns]
            .describe()
            .transpose()
            .to_string()
        )

    print("\n" + "=" * 70)
    print("AUDIT COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
