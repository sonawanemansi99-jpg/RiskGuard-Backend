
import os
import joblib
import numpy as np
import pandas as pd

from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(
    BASE_DIR, "data", "post_drift_transactions.csv"
)

MODEL_PATH = os.path.join(
    BASE_DIR, "models", "riskguard_logistic_candidate.pkl"
)

df = pd.read_csv(DATA_PATH)

X = df.drop(
    columns=["is_fraud", "transaction_ref"],
    errors="ignore"
)

y = df["is_fraud"]

# Fresh reproducible split for this experiment
X_dev, X_test, y_dev, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=2026,
    stratify=y
)

X_train, X_val, y_train, y_val = train_test_split(
    X_dev,
    y_dev,
    test_size=0.25,
    random_state=2026,
    stratify=y_dev
)

numeric_features = [
    "amount",
    "hour",
    "new_device",
    "transactions_last_hour"
]

categorical_features = [
    "location",
    "merchant_category"
]

preprocessor = ColumnTransformer(
    transformers=[
        (
            "numeric",
            Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler())
            ]),
            numeric_features
        ),
        (
            "categorical",
            Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(handle_unknown="ignore"))
            ]),
            categorical_features
        )
    ]
)

pipeline = Pipeline([
    ("preprocessor", preprocessor),
    (
        "classifier",
        LogisticRegression(
            max_iter=3000,
            random_state=42
        )
    )
])

print("\n========== LOGISTIC REGRESSION EXPERIMENT ==========")

# Train on training split
pipeline.fit(X_train, y_train)

# Select threshold using validation data only
val_probabilities = pipeline.predict_proba(X_val)[:, 1]

thresholds = np.arange(0.10, 0.91, 0.01)

best_threshold = 0.50
best_f1 = -1

for threshold in thresholds:
    val_predictions = (
        val_probabilities >= threshold
    ).astype(int)

    score = f1_score(
        y_val,
        val_predictions,
        zero_division=0
    )

    if score > best_f1:
        best_f1 = score
        best_threshold = threshold

print("\nBest validation threshold:", round(best_threshold, 2))
print("Validation F1:", round(best_f1 * 100, 2), "%")

# Refit on complete development data
final_model = clone(pipeline)
final_model.fit(X_dev, y_dev)

# Evaluate once on the untouched test split
test_probabilities = final_model.predict_proba(X_test)[:, 1]

test_predictions = (
    test_probabilities >= best_threshold
).astype(int)

print("\n========== FINAL TEST RESULTS ==========")

print("Algorithm: Logistic Regression")
print("Test transactions:", len(X_test))
print("Threshold:", round(best_threshold, 2))

print(
    "Accuracy:",
    round(accuracy_score(y_test, test_predictions) * 100, 2), "%"
)

print(
    "Precision:",
    round(precision_score(y_test, test_predictions, zero_division=0) * 100, 2), "%"
)

print(
    "Fraud Recall:",
    round(recall_score(y_test, test_predictions, zero_division=0) * 100, 2), "%"
)

print(
    "F1 Score:",
    round(f1_score(y_test, test_predictions, zero_division=0) * 100, 2), "%"
)

print(
    "ROC-AUC:",
    round(roc_auc_score(y_test, test_probabilities) * 100, 2), "%"
)

print(
    "PR-AUC:",
    round(average_precision_score(y_test, test_probabilities) * 100, 2), "%"
)

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, test_predictions))

# Save as a separate candidate
final_model.risk_threshold_ = best_threshold

joblib.dump(final_model, MODEL_PATH)

print("\nCandidate saved successfully:")
print(MODEL_PATH)

print("\n========== EXPERIMENT COMPLETED ==========")
