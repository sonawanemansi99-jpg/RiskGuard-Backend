
import os
import joblib
import numpy as np
import pandas as pd

from sklearn.base import clone
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

GB_PATH = os.path.join(
    BASE_DIR, "models", "riskguard_improved_candidate.pkl"
)

df = pd.read_csv(DATA_PATH)

X = df.drop(
    columns=["is_fraud", "transaction_ref"],
    errors="ignore"
)
y = df["is_fraud"]

# Same split for both algorithms
X_dev, X_test, y_dev, y_test = train_test_split(
    X, y,
    test_size=0.20,
    random_state=31415,
    stratify=y
)

X_train, X_val, y_train, y_val = train_test_split(
    X_dev, y_dev,
    test_size=0.25,
    random_state=31415,
    stratify=y_dev
)

gb_template = joblib.load(GB_PATH)

thresholds = np.arange(0.10, 0.91, 0.01)

def tune_threshold(model, X_validation, y_validation):
    probabilities = model.predict_proba(X_validation)[:, 1]

    best_threshold = 0.50
    best_score = -1

    for threshold in thresholds:
        predictions = (
            probabilities >= threshold
        ).astype(int)

        score = f1_score(
            y_validation,
            predictions,
            zero_division=0
        )

        if score > best_score:
            best_score = score
            best_threshold = threshold

    return best_threshold, best_score


print("\n========== FAIR MODEL COMPARISON ==========")

# ---------------------------------------
# 1. Tune Logistic Regression
# ---------------------------------------

best_lr = None
best_lr_c = None
best_lr_threshold = None
best_lr_f1 = -1

for c_value in [0.01, 0.1, 1, 10, 100, 1000]:

    model = clone(gb_template)

    model.set_params(
        classifier=LogisticRegression(
            C=c_value,
            max_iter=5000,
            random_state=42
        )
    )

    model.fit(X_train, y_train)

    threshold, score = tune_threshold(
        model, X_val, y_val
    )

    print(
        f"Logistic C={c_value}: "
        f"Validation F1={score * 100:.2f}%"
    )

    if score > best_lr_f1:
        best_lr = clone(model)
        best_lr_c = c_value
        best_lr_threshold = threshold
        best_lr_f1 = score


# ---------------------------------------
# 2. Tune Gradient Boosting threshold
# ---------------------------------------

gb_model = clone(gb_template)
gb_model.fit(X_train, y_train)

gb_threshold, gb_validation_f1 = tune_threshold(
    gb_model, X_val, y_val
)

print("\nSelected Logistic C:", best_lr_c)
print("Logistic threshold:", round(best_lr_threshold, 2))
print("Gradient Boosting threshold:", round(gb_threshold, 2))

# ---------------------------------------
# 3. Refit both on development data
# ---------------------------------------

best_lr.fit(X_dev, y_dev)

gb_model = clone(gb_template)
gb_model.fit(X_dev, y_dev)

models = [
    ("Logistic Regression", best_lr, best_lr_threshold),
    ("Gradient Boosting", gb_model, gb_threshold)
]

# ---------------------------------------
# 4. Final test evaluation
# ---------------------------------------

for name, model, threshold in models:

    probabilities = model.predict_proba(X_test)[:, 1]

    predictions = (
        probabilities >= threshold
    ).astype(int)

    print(f"\n========== {name} ==========")

    print("Threshold:", round(threshold, 2))

    print(
        "Accuracy:",
        round(accuracy_score(y_test, predictions) * 100, 2), "%"
    )

    print(
        "Precision:",
        round(precision_score(y_test, predictions, zero_division=0) * 100, 2), "%"
    )

    print(
        "Fraud Recall:",
        round(recall_score(y_test, predictions, zero_division=0) * 100, 2), "%"
    )

    print(
        "F1 Score:",
        round(f1_score(y_test, predictions, zero_division=0) * 100, 2), "%"
    )

    print(
        "ROC-AUC:",
        round(roc_auc_score(y_test, probabilities) * 100, 2), "%"
    )

    print(
        "PR-AUC:",
        round(average_precision_score(y_test, probabilities) * 100, 2), "%"
    )

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, predictions))

print("\n========== COMPARISON COMPLETED ==========")
print("No existing models were overwritten.")
