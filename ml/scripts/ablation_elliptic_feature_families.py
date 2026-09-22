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
    "ml/datasets/processed/elliptic_plus_plus/elliptic_behavioral.csv"
)

RANDOM_STATE = 42
N_SPLITS = 5
N_ESTIMATORS = 300


def get_feature_groups(feature_columns):
    """
    Group the 102 behavioral features into interpretable
    blockchain-behavior families.
    """

    groups = {
        "activity": [],
        "value_flow": [],
        "fees": [],
        "counterparty": [],
        "transaction_spacing": [],
    }

    for column in feature_columns:

        lower = column.lower()

        # --------------------------------------------------------
        # Activity
        # --------------------------------------------------------

        if (
            lower.startswith("num_txs_as_sender")
            or lower.startswith("num_txs_as receiver")
            or lower.startswith("total_txs")
            or lower.startswith("lifetime_in_blocks")
            or lower.startswith("num_timesteps_appeared_in")
        ):
            groups["activity"].append(column)

        # --------------------------------------------------------
        # Value flow
        # --------------------------------------------------------

        elif (
            lower.startswith("btc_transacted")
            or lower.startswith("btc_sent")
            or lower.startswith("btc_received")
        ):
            groups["value_flow"].append(column)

        # --------------------------------------------------------
        # Fees
        # --------------------------------------------------------

        elif (
            lower.startswith("fees_")
            or lower.startswith("fees_as_share")
        ):
            groups["fees"].append(column)

        # --------------------------------------------------------
        # Counterparty / network
        # --------------------------------------------------------

        elif (
            lower.startswith("num_addr_transacted_multiple")
            or lower.startswith("transacted_w_address")
        ):
            groups["counterparty"].append(column)

        # --------------------------------------------------------
        # Transaction spacing
        # --------------------------------------------------------

        elif (
            lower.startswith("blocks_btwn_txs")
            or lower.startswith("blocks_btwn_input_txs")
            or lower.startswith("blocks_btwn_output_txs")
        ):
            groups["transaction_spacing"].append(column)

        else:
            print(
                f"WARNING: Feature not assigned to a group: "
                f"{column}"
            )

    return groups


def evaluate_model(
    name,
    df,
    feature_columns,
):
    print("\n" + "=" * 75)
    print(f"MODEL: {name}")
    print("=" * 75)

    X = df[feature_columns]
    y = df["target"]

    print(
        f"Rows:     {len(df):,}"
    )

    print(
        f"Features: {len(feature_columns):,}"
    )

    model = RandomForestClassifier(
        n_estimators=N_ESTIMATORS,
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

    for fold, (
        train_idx,
        test_idx,
    ) in enumerate(
        cv.split(X, y),
        start=1,
    ):

        print(
            f"\nFold {fold}/{N_SPLITS}"
        )

        X_train = X.iloc[train_idx]
        X_test = X.iloc[test_idx]

        y_train = y.iloc[train_idx]
        y_test = y.iloc[test_idx]

        fold_model = clone(model)

        fold_model.fit(
            X_train,
            y_train,
        )

        probabilities = (
            fold_model.predict_proba(
                X_test
            )[:, 1]
        )

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

        metrics["precision"].append(
            precision
        )

        metrics["recall"].append(
            recall
        )

        metrics["f1"].append(
            f1
        )

        metrics["roc_auc"].append(
            roc_auc
        )

        metrics["pr_auc"].append(
            pr_auc
        )

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
            np.std(
                values,
                ddof=1,
            )
        )

        results[metric_name] = mean_value

        print(
            f"{metric_name.upper():<12} "
            f"{mean_value:.4f} "
            f"+/- {std_value:.4f}"
        )

    return results


def main():
    print("=" * 75)
    print("ELLIPTIC++ FEATURE-FAMILY ABLATION")
    print("=" * 75)

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    df = pd.read_csv(
        DATA_PATH
    )

    feature_columns = [
        column
        for column in df.columns
        if column not in {
            "address",
            "target",
        }
        and pd.api.types.is_numeric_dtype(
            df[column]
        )
    ]

    print("\nDataset:")
    print(
        f"Rows:     {len(df):,}"
    )

    print(
        f"Features: {len(feature_columns):,}"
    )

    # ------------------------------------------------------------
    # Feature groups
    # ------------------------------------------------------------

    groups = get_feature_groups(
        feature_columns
    )

    print("\n" + "-" * 75)
    print("FEATURE GROUPS")
    print("-" * 75)

    for group_name, columns in groups.items():

        print(
            f"\n{group_name.upper()}: "
            f"{len(columns)} features"
        )

        for column in columns:
            print(
                f"  - {column}"
            )

    total_grouped = sum(
        len(columns)
        for columns in groups.values()
    )

    print(
        f"\nTotal grouped features: "
        f"{total_grouped}"
    )

    if total_grouped != len(
        feature_columns
    ):
        raise ValueError(
            "Not all behavioral features were "
            "assigned to a feature group."
        )

    # ------------------------------------------------------------
    # Full model
    # ------------------------------------------------------------

    results = {}

    results["full_model"] = evaluate_model(
        "FULL — ALL BEHAVIORAL FEATURES",
        df,
        feature_columns,
    )

    # ------------------------------------------------------------
    # Leave-one-family-out experiments
    # ------------------------------------------------------------

    for group_name, removed_features in (
        groups.items()
    ):

        remaining_features = [
            feature
            for feature in feature_columns
            if feature not in removed_features
        ]

        results[
            f"without_{group_name}"
        ] = evaluate_model(
            (
                "WITHOUT "
                + group_name.upper()
            ),
            df,
            remaining_features,
        )

    # ------------------------------------------------------------
    # Final comparison
    # ------------------------------------------------------------

    print("\n" + "=" * 75)
    print("FINAL FEATURE-FAMILY COMPARISON")
    print("=" * 75)

    comparison = pd.DataFrame(
        results
    ).T

    print(
        comparison.to_string(
            float_format=lambda x: f"{x:.4f}"
        )
    )

    # ------------------------------------------------------------
    # Performance changes
    # ------------------------------------------------------------

    baseline = results[
        "full_model"
    ]

    print("\n" + "=" * 75)
    print("CHANGE FROM FULL MODEL")
    print("=" * 75)

    for model_name, model_results in (
        results.items()
    ):

        if model_name == "full_model":
            continue

        print(
            f"\n{model_name}"
        )

        for metric in [
            "precision",
            "recall",
            "f1",
            "roc_auc",
            "pr_auc",
        ]:

            change = (
                model_results[metric]
                - baseline[metric]
            )

            print(
                f"  {metric.upper():<10} "
                f"{change:+.4f}"
            )

    print("\n" + "=" * 75)
    print("IMPORTANT")
    print("=" * 75)

    print(
        "This is feature-family research validation."
    )

    print(
        "Removing a feature family does not prove "
        "that the family is causally responsible "
        "for model behavior."
    )

    print(
        "These results are not production AML "
        "probabilities or definitive determinations."
    )

    print("=" * 75)


if __name__ == "__main__":
    main()