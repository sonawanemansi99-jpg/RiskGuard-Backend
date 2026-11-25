
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

# Use the three variables in the synthetic fraud formula
features = [
    "amount",
    "new_device",
    "transactions_last_hour"
]

X = df[features]
y = df["is_fraud"]

# 80% development data, 20% final test data
X_dev, X_test, y_dev, y_test = train_test_split(
    X, y,
    test_size=0.20,
    random_state=31415,
    stratify=y
)

# Split development data into training and validation
X_train, X_val, y_train, y_val = train_test_split(
    X_dev, y_dev,
    test_size=0.25,
    random_state=31415,
    stratify=y_dev
)

# Logistic Regression without class balancing
model = Pipeline([
    ("scaler", StandardScaler()),
    ("classifier", LogisticRegression(
        C=1.0,
        max_iter=5000,
        random_state=42
    ))
])

print("\n========== ACCURACY-OPTIMIZED LOGISTIC REGRESSION ==========")

model.fit(X_train, y_train)

# Tune threshold using validation accuracy
val_probabilities = model.predict_proba(X_val)[:, 1]

best_threshold = 0.50
best_accuracy = -1

for threshold in np.arange(0.10, 0.91, 0.01):

    predictions = (
        val_probabilities >= threshold
    ).astype(int)

    accuracy = accuracy_score(y_val, predictions)

    if accuracy > best_accuracy:
        best_accuracy = accuracy
        best_threshold = threshold

print("\nBest validation accuracy:", round(best_accuracy * 100, 2), "%")
print("Accuracy-optimized threshold:", round(best_threshold, 2))

# Refit on complete development data
model.fit(X_dev, y_dev)

test_probabilities = model.predict_proba(X_test)[:, 1]

# Compare default and accuracy-optimized thresholds
thresholds = {
    "Default threshold": 0.50,
    "Accuracy-optimized threshold": best_threshold
}

for name, threshold in thresholds.items():

    predictions = (
        test_probabilities >= threshold
    ).astype(int)

    print("\n==========", name, "==========")
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

print("\nROC-AUC:", round(roc_auc_score(y_test, test_probabilities) * 100, 2), "%")
print("PR-AUC:", round(average_precision_score(y_test, test_probabilities) * 100, 2), "%")

print("\n========== EXPERIMENT COMPLETED ==========")
print("No existing models were overwritten.")
