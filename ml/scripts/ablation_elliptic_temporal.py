from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold


DATA_PATH = Path(
    "ml/datasets/processed/elliptic_plus_plus/elliptic_wallet_validation.csv"
)

RANDOM_STATE = 42
N_SPLITS = 5


# These describe where the wallet appeared in the historical
# blockchain/dataset timeline.
DATASET_POSITION_FEATURES = {
    "first_block_appeared_in_mean",
    "first_block_appeared_in_max",
    "last_block_appeared_in_mean",
    "last_block_appeared_in_max",
    "first_sent_block_mean",
    "first_sent_block_max",
    "first_received_block_mean",
    "first_received_block_max",
    "first_time_step",
    "last_time_step",
}


# These describe how long / across how many temporal observations
# the wallet was active.
TEMPORAL_BEHAVIOR_FEATURES = {
    "time_steps_observed",
}


def run_experiment(
    name: str,
    df: pd.DataFrame,
    feature_columns: list[str],
) -> dict[str, float]:

    print("\n" + "=" * 75)
    print(f"MODEL: {name}")
    print("=" * 75)

    X = df[feature_columns]
    y = df["target"]

    print(f"Rows:     {len(df):,}")
    print(f"Features: {len(feature_columns):,}")

    model = RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    cv = StratifiedKFold(
        n_splits=N_SPLITS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    metrics = {
        "precision": [],
        "recall": [],
        "f1": [],
        "roc_auc": [],
        "pr_auc": [],
    }

    for fold, (train_idx, test_idx) in enumerate(
        cv.split(X, y),
        start=1,
    ):

        print(f"\nFold {fold}/{N_SPLITS}")

        X_train = X.iloc[train_idx]
        X_test = X.iloc[test_idx]

        y_train = y.iloc[train_idx]
        y_test = y.iloc[test_idx]

        fold_model = clone(model)

        fold_model.fit(
            X_train,
            y_train,
        )

        probabilities = fold_model.predict_proba(
            X_test
        )[:, 1]

        predictions = (
            probabilities >= 0.5
        ).astype(int)

        precision = precision_score(
            y_test,
            predictions,
            zero_division=0,
        )

        recall = recall_score(
            y_test,
            predictions,
            zero_division=0,
        )

        f1 = f1_score(
            y_test,
            predictions,
            zero_division=0,
        )

        roc_auc = roc_auc_score(
            y_test,
            probabilities,
        )

        pr_auc = average_precision_score(
            y_test,
            probabilities,
        )

        metrics["precision"].append(precision)
        metrics["recall"].append(recall)
        metrics["f1"].append(f1)
        metrics["roc_auc"].append(roc_auc)
        metrics["pr_auc"].append(pr_auc)

        print(
            f"  Precision: {precision:.4f}"
        )
        print(
            f"  Recall:    {recall:.4f}"
        )
        print(
            f"  F1:        {f1:.4f}"
        )
        print(
            f"  ROC-AUC:   {roc_auc:.4f}"
        )
        print(
            f"  PR-AUC:    {pr_auc:.4f}"
        )

    print("\n" + "-" * 75)
    print(f"{name} — SUMMARY")
    print("-" * 75)

    results = {}

    for metric_name, values in metrics.items():

        mean_value = float(
            np.mean(values)
        )

        std_value = float(
            np.std(values, ddof=1)
        )

        results[metric_name] = mean_value

        print(
            f"{metric_name.upper():<12} "
            f"{mean_value:.4f} "
            f"+/- {std_value:.4f}"
        )

    return results


def main() -> None:

    print("=" * 75)
    print("ELLIPTIC++ TEMPORAL ABLATION EXPERIMENT")
    print("=" * 75)

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    df = pd.read_csv(DATA_PATH)

    print("\nDataset:")
    print(f"Rows:    {len(df):,}")
    print(f"Columns: {len(df.columns):,}")

    all_numeric_features = [
        column
        for column in df.columns
        if column not in {"address", "target"}
        and pd.api.types.is_numeric_dtype(df[column])
    ]

    dataset_position = [
        column
        for column in all_numeric_features
        if column in DATASET_POSITION_FEATURES
    ]

    temporal_behavior = [
        column
        for column in all_numeric_features
        if column in TEMPORAL_BEHAVIOR_FEATURES
    ]

    behavioral_features = [
        column
        for column in all_numeric_features
        if column not in DATASET_POSITION_FEATURES
        and column not in TEMPORAL_BEHAVIOR_FEATURES
    ]

    # Preserve source-column order.
    behavioral_features = [
        column
        for column in df.columns
        if column in behavioral_features
    ]

    dataset_position = [
        column
        for column in df.columns
        if column in dataset_position
    ]

    temporal_behavior = [
        column
        for column in df.columns
        if column in temporal_behavior
    ]

    print("\nFeature groups:")
    print(
        f"Behavioral:             {len(behavioral_features)}"
    )
    print(
        f"Dataset-position:       {len(dataset_position)}"
    )
    print(
        f"Temporal behavior:      {len(temporal_behavior)}"
    )

    print("\nDataset-position features:")

    for feature in dataset_position:
        print(f"  - {feature}")

    print("\nTemporal-behavior features:")

    for feature in temporal_behavior:
        print(f"  - {feature}")

    # ------------------------------------------------------------
    # Three controlled experiments
    # ------------------------------------------------------------

    behavioral_results = run_experiment(
        "BEHAVIORAL ONLY",
        df,
        behavioral_features,
    )

    position_results = run_experiment(
        "BEHAVIORAL + DATASET POSITION",
        df,
        behavioral_features + dataset_position,
    )

    temporal_behavior_results = run_experiment(
        "BEHAVIORAL + TEMPORAL BEHAVIOR",
        df,
        behavioral_features + temporal_behavior,
    )

    # ------------------------------------------------------------
    # Final comparison
    # ------------------------------------------------------------

    print("\n" + "=" * 75)
    print("FINAL ABLATION COMPARISON")
    print("=" * 75)

    comparison = pd.DataFrame(
        {
            "behavioral_only": behavioral_results,
            "behavioral_plus_dataset_position": position_results,
            "behavioral_plus_temporal_behavior": temporal_behavior_results,
        }
    )

    print(
        comparison.to_string(
            float_format=lambda x: f"{x:.4f}"
        )
    )

    print("\n" + "=" * 75)
    print("INTERPRETATION GUIDE")
    print("=" * 75)

    print(
        "If dataset-position features produce most of the improvement, "
        "the earlier temporal gain may contain dataset-specific time effects."
    )

    print(
        "If temporal-behavior features improve performance independently, "
        "that supports the usefulness of genuine temporal behavior."
    )

    print(
        "These results are research validation only and are not "
        "production AML probabilities or definitive determinations."
    )

    print("=" * 75)


if __name__ == "__main__":
    main()