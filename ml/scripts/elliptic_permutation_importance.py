from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import average_precision_score
from sklearn.model_selection import StratifiedKFold


DATA_PATH = Path(
    "ml/datasets/processed/elliptic_plus_plus/elliptic_behavioral.csv"
)

RANDOM_STATE = 42

N_SPLITS = 5
N_ESTIMATORS = 300

# Much lighter than running permutation importance
# over the entire ~160k-row validation fold.
IMPORTANCE_SAMPLE_SIZE = 20_000

N_REPEATS = 2

N_JOBS = 2

TOP_FEATURES = 40


def main() -> None:

    print("=" * 75)
    print("ELLIPTIC++ EFFICIENT PERMUTATION IMPORTANCE")
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

    cv = StratifiedKFold(
        n_splits=N_SPLITS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    importance_records = []

    for fold, (train_idx, test_idx) in enumerate(
        cv.split(X, y),
        start=1,
    ):

        print("\n" + "-" * 75)
        print(f"FOLD {fold}/{N_SPLITS}")
        print("-" * 75)

        X_train = X.iloc[train_idx]
        X_test_full = X.iloc[test_idx]

        y_train = y.iloc[train_idx]
        y_test_full = y.iloc[test_idx]

        print(
            f"Training rows:   {len(X_train):,}"
        )

        print(
            f"Validation rows: {len(X_test_full):,}"
        )

        # --------------------------------------------------------
        # Train model on the complete training fold
        # --------------------------------------------------------

        model = RandomForestClassifier(
            n_estimators=N_ESTIMATORS,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=N_JOBS,
        )

        print("\nTraining Random Forest...")

        model.fit(
            X_train,
            y_train,
        )

        # --------------------------------------------------------
        # Baseline on full validation fold
        # --------------------------------------------------------

        baseline_probabilities = model.predict_proba(
            X_test_full
        )[:, 1]

        baseline_pr_auc = average_precision_score(
            y_test_full,
            baseline_probabilities,
        )

        print(
            f"Full validation PR-AUC: "
            f"{baseline_pr_auc:.4f}"
        )

        # --------------------------------------------------------
        # Stratified validation sample
        # --------------------------------------------------------

        validation_sample_size = min(
            IMPORTANCE_SAMPLE_SIZE,
            len(X_test_full),
        )

        rng = np.random.RandomState(
            RANDOM_STATE + fold
        )

        sampled_indices = []

        for target_class in sorted(
            y_test_full.unique()
        ):

            class_indices = np.flatnonzero(
                y_test_full.to_numpy()
                == target_class
            )

            class_fraction = (
                len(class_indices)
                / len(y_test_full)
            )

            class_sample_size = max(
                1,
                int(
                    round(
                        validation_sample_size
                        * class_fraction
                    )
                ),
            )

            class_sample_size = min(
                class_sample_size,
                len(class_indices),
            )

            selected = rng.choice(
                class_indices,
                size=class_sample_size,
                replace=False,
            )

            sampled_indices.extend(
                selected.tolist()
            )

        sampled_indices = np.array(
            sampled_indices,
            dtype=int,
        )

        X_test = X_test_full.iloc[
            sampled_indices
        ]

        y_test = y_test_full.iloc[
            sampled_indices
        ]

        print(
            f"Permutation sample: "
            f"{len(X_test):,} rows"
        )

        print(
            "Calculating permutation importance..."
        )

        # --------------------------------------------------------
        # Permutation importance
        # --------------------------------------------------------

        result = permutation_importance(
            model,
            X_test,
            y_test,
            scoring="average_precision",
            n_repeats=N_REPEATS,
            random_state=RANDOM_STATE,
            n_jobs=N_JOBS,
        )

        for index, feature in enumerate(
            feature_columns
        ):

            importance_records.append(
                {
                    "fold": fold,
                    "feature": feature,
                    "importance_mean": (
                        result.importances_mean[index]
                    ),
                    "importance_std": (
                        result.importances_std[index]
                    ),
                }
            )

        fold_importance = pd.DataFrame(
            {
                "feature": feature_columns,
                "importance": (
                    result.importances_mean
                ),
            }
        ).sort_values(
            "importance",
            ascending=False,
        )

        print("\nTop 15 features for this fold:")

        for rank, (_, row) in enumerate(
            fold_importance.head(15).iterrows(),
            start=1,
        ):

            print(
                f"  {rank:2d}. "
                f"{row['importance']:+.6f}  "
                f"{row['feature']}"
            )

    # ------------------------------------------------------------
    # Aggregate results
    # ------------------------------------------------------------

    importance_df = pd.DataFrame(
        importance_records
    )

    summary = (
        importance_df
        .groupby("feature")
        .agg(
            mean_importance=(
                "importance_mean",
                "mean",
            ),
            std_importance=(
                "importance_mean",
                "std",
            ),
            mean_repeat_std=(
                "importance_std",
                "mean",
            ),
        )
        .reset_index()
        .sort_values(
            "mean_importance",
            ascending=False,
        )
    )

    print("\n" + "=" * 75)
    print(
        f"TOP {TOP_FEATURES} FEATURES "
        "BY PERMUTATION IMPORTANCE"
    )
    print("=" * 75)

    for rank, (_, row) in enumerate(
        summary.head(TOP_FEATURES).iterrows(),
        start=1,
    ):

        print(
            f"{rank:2d}. "
            f"{row['mean_importance']:+.6f} "
            f"+/- {row['std_importance']:.6f}  "
            f"{row['feature']}"
        )

    # --------------------------------------------------------
    # Negative importance
    # --------------------------------------------------------

    negative_features = summary[
        summary["mean_importance"] < 0
    ]

    print("\n" + "-" * 75)
    print("NEGATIVE MEAN PERMUTATION IMPORTANCE")
    print("-" * 75)

    print(
        f"Count: {len(negative_features):,}"
    )

    for _, row in negative_features.head(
        20
    ).iterrows():

        print(
            f"  {row['mean_importance']:+.6f}  "
            f"{row['feature']}"
        )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    output_dir = Path(
        "ml/datasets/processed/elliptic_plus_plus"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        output_dir
        / "elliptic_permutation_importance.csv"
    )

    summary.to_csv(
        output_path,
        index=False,
    )

    print("\n" + "-" * 75)
    print("OUTPUT")
    print("-" * 75)

    print(
        f"Saved:\n  {output_path}"
    )

    print("\n" + "=" * 75)
    print("PERMUTATION IMPORTANCE AUDIT COMPLETE")
    print("=" * 75)


if __name__ == "__main__":
    main()