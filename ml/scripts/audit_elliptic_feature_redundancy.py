from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier


DATA_PATH = Path(
    "ml/datasets/processed/elliptic_plus_plus/elliptic_behavioral.csv"
)

RANDOM_STATE = 42
N_ESTIMATORS = 300

# Correlation threshold for identifying highly redundant features.
CORRELATION_THRESHOLD = 0.98

# Number of top features to display.
TOP_FEATURES = 30


def main() -> None:
    print("=" * 75)
    print("ELLIPTIC++ FEATURE REDUNDANCY & IMPORTANCE AUDIT")
    print("=" * 75)

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH)

    feature_columns = [
        column
        for column in df.columns
        if column not in {"address", "target"}
        and pd.api.types.is_numeric_dtype(df[column])
    ]

    X = df[feature_columns]
    y = df["target"]

    print("\nDataset:")
    print(f"Rows:     {len(df):,}")
    print(f"Features: {len(feature_columns):,}")

    # ------------------------------------------------------------
    # 1. Exact duplicate feature columns
    # ------------------------------------------------------------

    print("\n" + "-" * 75)
    print("1. EXACT DUPLICATE FEATURE COLUMNS")
    print("-" * 75)

    duplicate_groups = []

    seen = {}

    for column in feature_columns:
        values = tuple(X[column].values)

        if values in seen:
            duplicate_groups.append(
                (seen[values], column)
            )
        else:
            seen[values] = column

    if duplicate_groups:
        for first, duplicate in duplicate_groups:
            print(
                f"  {duplicate} == {first}"
            )
    else:
        print("  No exact duplicate feature columns found.")

    # ------------------------------------------------------------
    # 2. Highly correlated feature pairs
    # ------------------------------------------------------------

    print("\n" + "-" * 75)
    print(
        f"2. HIGHLY CORRELATED FEATURE PAIRS "
        f"(absolute correlation >= {CORRELATION_THRESHOLD})"
    )
    print("-" * 75)

    correlation_matrix = X.corr()

    highly_correlated = []

    for i, column_a in enumerate(feature_columns):
        for j in range(i + 1, len(feature_columns)):
            column_b = feature_columns[j]

            correlation = correlation_matrix.loc[
                column_a,
                column_b,
            ]

            if abs(correlation) >= CORRELATION_THRESHOLD:
                highly_correlated.append(
                    (
                        column_a,
                        column_b,
                        correlation,
                    )
                )

    highly_correlated.sort(
        key=lambda item: abs(item[2]),
        reverse=True,
    )

    print(
        f"Found {len(highly_correlated):,} highly "
        "correlated feature pairs."
    )

    for column_a, column_b, correlation in (
        highly_correlated[:100]
    ):
        print(
            f"  {correlation:+.5f}  "
            f"{column_a}  <->  {column_b}"
        )

    if len(highly_correlated) > 100:
        print(
            f"\n  ... showing first 100 of "
            f"{len(highly_correlated):,}"
        )

    # ------------------------------------------------------------
    # 3. Feature variance
    # ------------------------------------------------------------

    print("\n" + "-" * 75)
    print("3. ZERO / NEAR-ZERO VARIANCE FEATURES")
    print("-" * 75)

    variance = X.var()

    zero_variance = [
        column
        for column in feature_columns
        if variance[column] == 0
    ]

    near_zero_variance = [
        column
        for column in feature_columns
        if variance[column] > 0
        and variance[column] < 1e-8
    ]

    print(
        f"Zero variance:       {len(zero_variance)}"
    )

    for column in zero_variance:
        print(f"  - {column}")

    print(
        f"Near-zero variance:  {len(near_zero_variance)}"
    )

    for column in near_zero_variance:
        print(f"  - {column}")

    # ------------------------------------------------------------
    # 4. Random Forest feature importance
    # ------------------------------------------------------------

    print("\n" + "-" * 75)
    print(
        f"4. RANDOM FOREST FEATURE IMPORTANCE "
        f"(top {TOP_FEATURES})"
    )
    print("-" * 75)

    model = RandomForestClassifier(
        n_estimators=N_ESTIMATORS,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    print(
        "\nTraining Random Forest for importance analysis..."
    )

    model.fit(X, y)

    importance = pd.DataFrame(
        {
            "feature": feature_columns,
            "importance": model.feature_importances_,
        }
    )

    importance = importance.sort_values(
        "importance",
        ascending=False,
    ).reset_index(drop=True)

    for index, row in importance.head(
        TOP_FEATURES
    ).iterrows():

        print(
            f"  {index + 1:2d}. "
            f"{row['importance']:.6f}  "
            f"{row['feature']}"
        )

    # ------------------------------------------------------------
    # 5. Importance concentration
    # ------------------------------------------------------------

    print("\n" + "-" * 75)
    print("5. FEATURE IMPORTANCE CONCENTRATION")
    print("-" * 75)

    total_importance = importance[
        "importance"
    ].sum()

    for count in [5, 10, 20, 30, 50]:

        if count <= len(importance):

            share = (
                importance.head(count)[
                    "importance"
                ].sum()
                / total_importance
            )

            print(
                f"Top {count:2d} features: "
                f"{share:.2%} of total importance"
            )

    # ------------------------------------------------------------
    # 6. Target association
    # ------------------------------------------------------------

    print("\n" + "-" * 75)
    print("6. ABSOLUTE CORRELATION WITH TARGET")
    print("-" * 75)

    target_correlations = (
        X.assign(target=y)
        .corr()["target"]
        .drop("target")
        .abs()
        .sort_values(
            ascending=False
        )
    )

    for feature, value in target_correlations.head(
        TOP_FEATURES
    ).items():

        print(
            f"  {value:.6f}  {feature}"
        )

    # ------------------------------------------------------------
    # 7. Save audit outputs
    # ------------------------------------------------------------

    output_dir = Path(
        "ml/datasets/processed/elliptic_plus_plus"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    importance_path = (
        output_dir
        / "elliptic_feature_importance.csv"
    )

    correlation_path = (
        output_dir
        / "elliptic_feature_correlations.csv"
    )

    importance.to_csv(
        importance_path,
        index=False,
    )

    correlation_output = pd.DataFrame(
        highly_correlated,
        columns=[
            "feature_a",
            "feature_b",
            "correlation",
        ],
    )

    correlation_output.to_csv(
        correlation_path,
        index=False,
    )

    print("\n" + "-" * 75)
    print("7. OUTPUT FILES")
    print("-" * 75)

    print(
        f"Feature importance:\n  {importance_path}"
    )

    print(
        f"Correlation pairs:\n  {correlation_path}"
    )

    print("\n" + "=" * 75)
    print("FEATURE AUDIT COMPLETE")
    print("=" * 75)


if __name__ == "__main__":
    main()