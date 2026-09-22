from pathlib import Path

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    average_precision_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


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

print("Loading dataset...")

df = pd.read_csv(DATA_PATH)

print("Dataset shape:", df.shape)


# =========================================================
# Separate features and target
# =========================================================

TARGET = "FLAG"

X = df.drop(columns=[TARGET])
y = df[TARGET]


print("\nTarget distribution:")
print(y.value_counts().to_string())


# =========================================================
# Identify feature types
# =========================================================

numeric_features = X.select_dtypes(
    include=["number"]
).columns.tolist()

categorical_features = X.select_dtypes(
    include=["object"]
).columns.tolist()


print("\nNumeric features:", len(numeric_features))
print("Categorical features:", len(categorical_features))

print("\nCategorical columns:")
print(categorical_features)


# =========================================================
# Preprocessing
# =========================================================

numeric_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="median"),
        )
    ]
)


categorical_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="most_frequent"),
        ),
        (
            "onehot",
            OneHotEncoder(
                handle_unknown="ignore",
            ),
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
        (
            "categorical",
            categorical_pipeline,
            categorical_features,
        ),
    ]
)


# =========================================================
# Train/test split
# =========================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)


print("\nTraining rows:", len(X_train))
print("Testing rows:", len(X_test))


# =========================================================
# Random Forest
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
# Train
# =========================================================

print("\nTraining Random Forest...")

pipeline.fit(
    X_train,
    y_train,
)


print("Training complete.")


# =========================================================
# Predictions
# =========================================================

y_pred = pipeline.predict(X_test)

y_probability = pipeline.predict_proba(X_test)[:, 1]


# =========================================================
# Classification report
# =========================================================

print("\n========================================")
print("CLASSIFICATION REPORT")
print("========================================")

print(
    classification_report(
        y_test,
        y_pred,
        digits=4,
    )
)


# =========================================================
# Confusion matrix
# =========================================================

print("========================================")
print("CONFUSION MATRIX")
print("========================================")

cm = confusion_matrix(
    y_test,
    y_pred,
)

print(cm)


# =========================================================
# ROC-AUC
# =========================================================

roc_auc = roc_auc_score(
    y_test,
    y_probability,
)

print("\nROC-AUC:", round(roc_auc, 4))


# =========================================================
# PR-AUC
# =========================================================

pr_auc = average_precision_score(
    y_test,
    y_probability,
)

print("PR-AUC:", round(pr_auc, 4))


# =========================================================
# Feature importance
# =========================================================

print("\n========================================")
print("TOP FEATURE IMPORTANCE")
print("========================================")

trained_preprocessor = pipeline.named_steps[
    "preprocessor"
]

trained_model = pipeline.named_steps[
    "model"
]

feature_names = (
    trained_preprocessor
    .get_feature_names_out()
)

importance = pd.Series(
    trained_model.feature_importances_,
    index=feature_names,
)

importance = importance.sort_values(
    ascending=False
)

print(
    importance.head(20).to_string()
)