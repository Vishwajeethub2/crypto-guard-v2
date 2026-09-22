from pathlib import Path

import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split, GroupShuffleSplit


# =========================================================
# Paths
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = (
    PROJECT_ROOT
    / "ml"
    / "datasets"
    / "raw"
    / "ethereum_fraud"
    / "transaction_dataset.csv"
)


# =========================================================
# Load
# =========================================================

df = pd.read_csv(DATA_PATH)

TARGET = "FLAG"

# Keep identifiers only for validation diagnostics.
X = df.drop(
    columns=[
        TARGET,
        "Unnamed: 0",
        "Index",
        "Address",
    ]
)

y = df[TARGET]


# =========================================================
# Helper function
# =========================================================

def run_model(
    X_train,
    X_test,
    y_train,
    y_test,
    name,
):
    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    # Keep only numeric features for this controlled experiment.
    numeric_train = X_train.select_dtypes(
        include="number"
    ).copy()

    numeric_test = X_test[
        numeric_train.columns
    ].copy()

    # Replace missing numeric values with training medians.
    medians = numeric_train.median()

    numeric_train = numeric_train.fillna(
        medians
    )

    numeric_test = numeric_test.fillna(
        medians
    )

    model = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        n_jobs=-1,
        class_weight="balanced",
    )

    model.fit(
        numeric_train,
        y_train,
    )

    predictions = model.predict(
        numeric_test
    )

    probabilities = model.predict_proba(
        numeric_test
    )[:, 1]

    print(
        classification_report(
            y_test,
            predictions,
            digits=4,
        )
    )

    print("Confusion matrix:")
    print(
        confusion_matrix(
            y_test,
            predictions,
        )
    )

    print(
        "ROC-AUC:",
        round(
            roc_auc_score(
                y_test,
                probabilities,
            ),
            4,
        ),
    )

    print(
        "PR-AUC:",
        round(
            average_precision_score(
                y_test,
                probabilities,
            ),
            4,
        ),
    )


# =========================================================
# Experiment 1
# Stratified random split
# =========================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)

run_model(
    X_train,
    X_test,
    y_train,
    y_test,
    "EXPERIMENT 1 - STRATIFIED RANDOM SPLIT",
)


# =========================================================
# Experiment 2
# Address-grouped split
# =========================================================

groups = df["Address"]

group_splitter = GroupShuffleSplit(
    n_splits=1,
    test_size=0.20,
    random_state=42,
)

train_idx, test_idx = next(
    group_splitter.split(
        X,
        y,
        groups=groups,
    )
)

X_train_group = X.iloc[train_idx]
X_test_group = X.iloc[test_idx]

y_train_group = y.iloc[train_idx]
y_test_group = y.iloc[test_idx]

run_model(
    X_train_group,
    X_test_group,
    y_train_group,
    y_test_group,
    "EXPERIMENT 2 - ADDRESS-GROUPED SPLIT",
)


# =========================================================
# Experiment 3
# Diagnostic: use Index as a feature
# =========================================================

X_with_index = df.drop(
    columns=[
        TARGET,
        "Unnamed: 0",
        "Address",
    ]
)

X_train_index, X_test_index, y_train_index, y_test_index = (
    train_test_split(
        X_with_index,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )
)

run_model(
    X_train_index,
    X_test_index,
    y_train_index,
    y_test_index,
    "EXPERIMENT 3 - DIAGNOSTIC WITH INDEX",
)


print("\n" + "=" * 60)
print("VALIDATION EXPERIMENT COMPLETE")
print("=" * 60)