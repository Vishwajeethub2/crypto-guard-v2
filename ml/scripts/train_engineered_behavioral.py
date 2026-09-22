from pathlib import Path

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = (
    PROJECT_ROOT
    / "ml"
    / "datasets"
    / "processed"
    / "ethereum_fraud"
    / "ethereum_fraud_model_ready.csv"
)


# =========================================================
# Load dataset
# =========================================================

df = pd.read_csv(INPUT_PATH)

print("=" * 80)
print("ENGINEERED BEHAVIORAL MODEL")
print("=" * 80)

print()
print("Dataset shape:", df.shape)


# =========================================================
# Remove target and non-behavioral categorical columns
# =========================================================

TARGET = "FLAG"

# These are categorical token identity/type fields.
# We intentionally exclude them so this remains a
# behavioral-only experiment.
TOKEN_COLUMNS = [
    "ERC20 most sent token type",
    "ERC20_most_rec_token_type",
]

X = df.drop(
    columns=[TARGET] + TOKEN_COLUMNS,
    errors="ignore",
)

y = df[TARGET]


# =========================================================
# Feature types
# =========================================================

numeric_features = X.select_dtypes(
    include=["number"]
).columns.tolist()

categorical_features = X.select_dtypes(
    include=["object"]
).columns.tolist()

print()
print("Numeric features:", len(numeric_features))
print("Categorical features:", len(categorical_features))


# =========================================================
# Preprocessing
# =========================================================

numeric_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="median"),
        ),
    ]
)

preprocessor = ColumnTransformer(
    transformers=[
        (
            "numeric",
            numeric_pipeline,
            numeric_features,
        ),
    ],
    remainder="drop",
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


pipeline = Pipeline(
    steps=[
        (
            "preprocessor",
            preprocessor,
        ),
        (
            "model",
            model,
        ),
    ]
)


# =========================================================
# Train / test split
# =========================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)


print()
print("Training rows:", len(X_train))
print("Testing rows :", len(X_test))

print()
print("Training class distribution:")
print(y_train.value_counts().sort_index())

print()
print("Testing class distribution:")
print(y_test.value_counts().sort_index())


# =========================================================
# Train
# =========================================================

print()
print("Training Random Forest...")

pipeline.fit(
    X_train,
    y_train,
)


# =========================================================
# Predictions
# =========================================================

y_pred = pipeline.predict(X_test)

y_probability = pipeline.predict_proba(
    X_test
)[:, 1]


# =========================================================
# Metrics
# =========================================================

accuracy = accuracy_score(
    y_test,
    y_pred,
)

precision = precision_score(
    y_test,
    y_pred,
    pos_label=1,
)

recall = recall_score(
    y_test,
    y_pred,
    pos_label=1,
)

f1 = f1_score(
    y_test,
    y_pred,
    pos_label=1,
)

roc_auc = roc_auc_score(
    y_test,
    y_probability,
)

pr_auc = average_precision_score(
    y_test,
    y_probability,
)


# =========================================================
# Results
# =========================================================

print()
print("=" * 80)
print("RESULTS")
print("=" * 80)

print(f"Accuracy       : {accuracy:.4f}")
print(f"Fraud Precision: {precision:.4f}")
print(f"Fraud Recall   : {recall:.4f}")
print(f"Fraud F1       : {f1:.4f}")
print(f"ROC-AUC        : {roc_auc:.4f}")
print(f"PR-AUC         : {pr_auc:.4f}")


# =========================================================
# Confusion matrix
# =========================================================

print()
print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))


# =========================================================
# Classification report
# =========================================================

print()
print("Classification Report:")
print(
    classification_report(
        y_test,
        y_pred,
        digits=4,
    )
)


# =========================================================
# Feature importance
# =========================================================

trained_model = pipeline.named_steps["model"]

importances = trained_model.feature_importances_

feature_importance = (
    pd.DataFrame(
        {
            "feature": numeric_features,
            "importance": importances,
        }
    )
    .sort_values(
        "importance",
        ascending=False,
    )
)

print()
print("=" * 80)
print("TOP 20 FEATURES")
print("=" * 80)

print(
    feature_importance.head(20).to_string(
        index=False
    )
)