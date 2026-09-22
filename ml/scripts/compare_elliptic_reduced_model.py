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


DATA_DIR = Path(
    "ml/datasets/processed/elliptic_plus_plus"
)

ORIGINAL_PATH = (
    DATA_DIR / "elliptic_behavioral.csv"
)

REDUCED_PATH = (
    DATA_DIR / "elliptic_behavioral_reduced.csv"
)

RANDOM_STATE = 42
N_SPLITS = 5


def evaluate_model(
    name: str,
    df: pd.DataFrame,
) -> dict[str, float]:

    print("\n" + "=" * 75)
    print(f"MODEL: {name}")
    print("=" * 75)

    X = df.drop(
        columns=["address", "target"]
    )

    y = df["target"]

    print(f"Rows:     {len(df):,}")
    print(f"Features: {X.shape[1]:,}")

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

    results = {}

    print("\n" + "-" * 75)
    print(f"{name} — SUMMARY")
    print("-" * 75)

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
    print("ELLIPTIC++ ORIGINAL VS REDUCED MODEL")
    print("=" * 75)

    if not ORIGINAL_PATH.exists():
        raise FileNotFoundError(
            f"Missing: {ORIGINAL_PATH}"
        )

    if not REDUCED_PATH.exists():
        raise FileNotFoundError(
            f"Missing: {REDUCED_PATH}"
        )

    original_df = pd.read_csv(
        ORIGINAL_PATH
    )

    reduced_df = pd.read_csv(
        REDUCED_PATH
    )

    original_results = evaluate_model(
        "ORIGINAL — 102 FEATURES",
        original_df,
    )

    reduced_results = evaluate_model(
        "REDUCED — 80 FEATURES",
        reduced_df,
    )

    print("\n" + "=" * 75)
    print("FINAL COMPARISON")
    print("=" * 75)

    comparison = pd.DataFrame(
        {
            "original_102": original_results,
            "reduced_80": reduced_results,
        }
    )

    print(
        comparison.to_string(
            float_format=lambda x: f"{x:.4f}"
        )
    )

    print("\n" + "=" * 75)
    print("NOTE")
    print("=" * 75)

    print(
        "The reduced dataset removes only exact duplicate "
        "feature columns."
    )

    print(
        "No production threshold or AML risk interpretation "
        "is being established here."
    )

    print("=" * 75)


if __name__ == "__main__":
    main()