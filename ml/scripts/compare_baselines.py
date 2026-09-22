from pathlib import Path

import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split


# =========================================================
# Paths
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = (
    PROJECT_ROOT
    / "ml"
    / "datasets"
    / "processed"
    / "ethereum_fraud"
    / "ethereum_fraud_clean.csv"
)


# =========================================================
# Load dataset
# =========================================================

df = pd.read_csv(DATA_PATH)

TARGET = "FLAG"

X = df.drop(columns=[TARGET])
y = df[TARGET]


# =========================================================
# Remove categorical token-name features
# =========================================================

CATEGORICAL_COLUMNS = [
    "ERC20 most sent token type",
    "ERC20_most_rec_token_type",
]

X_behavioral = X.drop(
    columns=CATEGORICAL_COLUMNS,
    errors="ignore",
)


# =========================================================
# Train/test split
# =========================================================

X_train, X_test, y_train, y_test = train_test_split(
    X_behavioral,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)


# =========================================================
# Model
# =========================================================

model = RandomForestClassifier(
    n_estimators=300,
    random_state=42,
    n_jobs=-1,
    class_weight="balanced",
)


# =========================================================
# Train
# =========================================================

print("Training behavioral-only Random Forest...")

model.fit(
    X_train,
    y_train,
)


# =========================================================
# Predictions
# =========================================================

y_pred = model.predict(X_test)

y_probability = model.predict_proba(X_test)[:, 1]


# =========================================================
# Metrics
# =========================================================

print("\n========================================")
print("BEHAVIORAL-ONLY BASELINE")
print("========================================")

print(
    classification_report(
        y_test,
        y_pred,
        digits=4,
    )
)

roc_auc = roc_auc_score(
    y_test,
    y_probability,
)

pr_auc = average_precision_score(
    y_test,
    y_probability,
)

print("ROC-AUC:", round(roc_auc, 4))
print("PR-AUC:", round(pr_auc, 4))


# =========================================================
# Feature importance
# =========================================================

importance = pd.Series(
    model.feature_importances_,
    index=X_behavioral.columns,
).sort_values(
    ascending=False
)

print("\n========================================")
print("TOP 20 BEHAVIORAL FEATURES")
print("========================================")

print(
    importance.head(20).to_string()
)