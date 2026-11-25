
import os
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
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

df = pd.read_csv(DATA_PATH)

# Features used by the synthetic fraud-generation formula
features = [
    "amount",
    "new_device",
    "transactions_last_hour"
]

X = df[features]
y = df["is_fraud"]

# Development and untouched test split
X_dev, X_test, y_dev, y_test = train_test_split(
    X, y,
    test_size=0.20,
    random_state=31415,
    stratify=y
)

# Training and validation split
X_train, X_val, y_train, y_val = train_test_split(
    X_dev, y_dev,
    test_size=0.25,
    random_state=31415,
    stratify=y_dev
)

C_VALUES = [
    0.001,
    0.01,
    0.1,
    1,
    10,
    100
]

THRESHOLDS = np.arange(0.30, 0.71, 0.01)

best_accuracy = -1
best_c = None
best_threshold = None

experiments = []

print("\n========== LOGISTIC REGRESSION ACCURACY TUNING ==========")

# -----------------------------------
# 1. Tune C and threshold
# -----------------------------------

for c_value in C_VALUES:

    model = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(
            C=c_value,
            max_iter=5000,
            random_state=42
        ))
    ])

    model.fit(X_train, y_train)

    val_probabilities = model.predict_proba(X_val)[:, 1]

    c_best_accuracy = -1
    c_best_threshold = 0.50

    for threshold in THRESHOLDS:

        predictions = (
            val_probabilities >= threshold
        ).astype(int)

        accuracy = accuracy_score(
            y_val,
            predictions
        )

        if accuracy > c_best_accuracy:
            c_best_accuracy = accuracy
            c_best_threshold = threshold

    print(
        f"C={c_value}: "
        f"Validation Accuracy={c_best_accuracy * 100:.2f}%, "
        f"Threshold={c_best_threshold:.2f}"
    )

    experiments.append({
        "C": c_value,
        "Validation Accuracy": c_best_accuracy,
        "Threshold": c_best_threshold
    })

    if c_best_accuracy > best_accuracy:
        best_accuracy = c_best_accuracy
        best_c = c_value
        best_threshold = c_best_threshold


# -----------------------------------
# 2. Display selected configuration
# -----------------------------------

print("\n========== BEST CONFIGURATION ==========")

print("Selected C:", best_c)
print("Selected threshold:", round(best_threshold, 2))
print("Best validation accuracy:", round(best_accuracy * 100, 2), "%")

print("\nAll validation results:")

print(
    pd.DataFrame(experiments).to_string(index=False)
)


# -----------------------------------
# 3. Train selected model on dev data
# -----------------------------------

final_model = Pipeline([
    ("scaler", StandardScaler()),
    ("classifier", LogisticRegression(
        C=best_c,
        max_iter=5000,
        random_state=42
    ))
])

final_model.fit(X_dev, y_dev)

test_probabilities = final_model.predict_proba(X_test)[:, 1]


# -----------------------------------
# 4. Evaluate on untouched test data
# -----------------------------------

print("\n========== FINAL TEST RESULTS ==========")

for name, threshold in [
    ("Default threshold", 0.50),
    ("Optimized threshold", best_threshold)
]:

    predictions = (
        test_probabilities >= threshold
    ).astype(int)

    print("\n", name)
    print("Threshold:", round(threshold, 2))

    print(
        "Accuracy:",
        round(accuracy_score(y_test, predictions) * 100, 2),
        "%"
    )

    print(
        "Precision:",
        round(precision_score(y_test, predictions, zero_division=0) * 100, 2),
        "%"
    )

    print(
        "Fraud Recall:",
        round(recall_score(y_test, predictions, zero_division=0) * 100, 2),
        "%"
    )

    print(
        "F1 Score:",
        round(f1_score(y_test, predictions, zero_division=0) * 100, 2),
        "%"
    )

    print("Confusion Matrix:")
    print(confusion_matrix(y_test, predictions))


print(
    "\nROC-AUC:",
    round(roc_auc_score(y_test, test_probabilities) * 100, 2),
    "%"
)

print(
    "PR-AUC:",
    round(average_precision_score(y_test, test_probabilities) * 100, 2),
    "%"
)

print("\n========== EXPERIMENT COMPLETED ==========")
print("No existing models were overwritten.")
