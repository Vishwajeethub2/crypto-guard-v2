from pathlib import Path

import pandas as pd


INPUT_PATH = Path(
    "ml/datasets/processed/elliptic_plus_plus/elliptic_behavioral.csv"
)

OUTPUT_PATH = Path(
    "ml/datasets/processed/elliptic_plus_plus/elliptic_behavioral_reduced.csv"
)


def main() -> None:
    print("=" * 75)
    print("ELLIPTIC++ EXACT-DUPLICATE FEATURE REDUCTION")
    print("=" * 75)

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input dataset not found: {INPUT_PATH}"
        )

    df = pd.read_csv(INPUT_PATH)

    print("\nOriginal dataset:")
    print(f"Rows:     {len(df):,}")
    print(f"Columns:  {len(df.columns):,}")

    feature_columns = [
        column
        for column in df.columns
        if column not in {"address", "target"}
    ]

    print(
        f"Original features: {len(feature_columns):,}"
    )

    # ------------------------------------------------------------
    # Find exact duplicate feature columns
    # ------------------------------------------------------------

    duplicate_columns = []

    seen_columns = {}

    for column in feature_columns:

        values = tuple(df[column].values)

        if values in seen_columns:

            original_column = seen_columns[values]

            duplicate_columns.append(
                column
            )

            print(
                f"\nDuplicate:"
                f"\n  keep:   {original_column}"
                f"\n  remove: {column}"
            )

        else:
            seen_columns[values] = column

    # ------------------------------------------------------------
    # Remove exact duplicates
    # ------------------------------------------------------------

    reduced_df = df.drop(
        columns=duplicate_columns
    ).copy()

    reduced_features = [
        column
        for column in reduced_df.columns
        if column not in {"address", "target"}
    ]

    print("\n" + "-" * 75)
    print("REDUCTION SUMMARY")
    print("-" * 75)

    print(
        f"Original features: "
        f"{len(feature_columns):,}"
    )

    print(
        f"Duplicate features removed: "
        f"{len(duplicate_columns):,}"
    )

    print(
        f"Remaining features: "
        f"{len(reduced_features):,}"
    )

    print(
        f"Rows: "
        f"{len(reduced_df):,}"
    )

    print(
        f"Missing values: "
        f"{reduced_df.isna().sum().sum():,}"
    )

    print(
        f"Duplicate rows: "
        f"{reduced_df.duplicated().sum():,}"
    )

    # ------------------------------------------------------------
    # Safety checks
    # ------------------------------------------------------------

    if reduced_df.isna().sum().sum() != 0:
        raise ValueError(
            "Reduced dataset contains missing values."
        )

    if reduced_df.duplicated().sum() != 0:
        raise ValueError(
            "Reduced dataset contains duplicate rows."
        )

    if reduced_df["address"].nunique() != len(
        reduced_df
    ):
        raise ValueError(
            "Address uniqueness changed unexpectedly."
        )

    # Target must remain unchanged.
    original_target = df["target"].reset_index(
        drop=True
    )

    reduced_target = reduced_df["target"].reset_index(
        drop=True
    )

    if not original_target.equals(
        reduced_target
    ):
        raise ValueError(
            "Target values changed during reduction."
        )

    # ------------------------------------------------------------
    # Save
    # ------------------------------------------------------------

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    reduced_df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print("\nSaved:")
    print(f"  {OUTPUT_PATH}")

    print("\n" + "=" * 75)
    print("EXACT-DUPLICATE REDUCTION COMPLETE")
    print("=" * 75)


if __name__ == "__main__":
    main()