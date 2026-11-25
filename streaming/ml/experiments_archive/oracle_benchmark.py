
import os
import numpy as np
import pandas as pd

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

df = pd.read_csv(DATA_PATH)

# Recreate the same test split
_, X_test, _, y_test = train_test_split(
    df.drop(columns=["is_fraud", "transaction_ref"]),
    df["is_fraud"],
    test_size=0.20,
    random_state=42,
    stratify=df["is_fraud"]
)

# Exact probability formula used by the dataset generator
risk = (
    -4.0
    + 2.0 * X_test["new_device"]
    + 0.6 * X_test["transactions_last_hour"]
    + 0.000015 * X_test["amount"]
)

oracle_probabilities = 1 / (1 + np.exp(-risk))

# Classify using the standard 0.50 threshold
oracle_predictions = (
    oracle_probabilities >= 0.50
).astype(int)

print("\n========== ORACLE BENCHMARK ==========")

print("\nExpected accuracy from probability estimates:")

expected_accuracy = np.mean(
    np.maximum(oracle_probabilities, 1 - oracle_probabilities)
)

print(f"{expected_accuracy * 100:.2f}%")

print("\nActual test-set performance:")

print(
    "Accuracy:",
    round(accuracy_score(y_test, oracle_predictions) * 100, 2), "%"
)

print(
    "Precision:",
    round(precision_score(y_test, oracle_predictions) * 100, 2), "%"
)

print(
    "Fraud Recall:",
    round(recall_score(y_test, oracle_predictions) * 100, 2), "%"
)

print(
    "F1 Score:",
    round(f1_score(y_test, oracle_predictions) * 100, 2), "%"
)

print(
    "ROC-AUC:",
    round(roc_auc_score(y_test, oracle_probabilities) * 100, 2), "%"
)

print(
    "PR-AUC:",
    round(average_precision_score(y_test, oracle_probabilities) * 100, 2), "%"
)

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, oracle_predictions))

print("\n========== BENCHMARK COMPLETED ==========")
