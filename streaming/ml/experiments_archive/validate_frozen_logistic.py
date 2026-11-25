
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
    confusion_matrix,
    classification_report
)

# -----------------------------------
# 1. Load dataset
# -----------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "post_drift_transactions.csv"
)

df = pd.read_csv(DATA_PATH)

features = [
    "amount",
    "new_device",
    "transactions_last_hour"
]

X = df[features]
y = df["is_fraud"]

print("\n========== FROZEN MODEL VALIDATION ==========")

print("Dataset size:", len(df))
print("Features:", features)

# -----------------------------------
# 2. Create a fresh split
# -----------------------------------

X_dev, X_test, y_dev, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=2026,
    stratify=y
)

print("\nDevelopment records:", len(X_dev))
print("Independent test records:", len(X_test))

# -----------------------------------
# 3. Freeze model configuration
# -----------------------------------

C_VALUE = 0.001
THRESHOLD = 0.40

model = Pipeline([
    ("scaler", StandardScaler()),
    ("classifier", LogisticRegression(
        C=C_VALUE,
        max_iter=5000,
        random_state=42
    ))
])

# -----------------------------------
# 4. Train only on development data
# -----------------------------------

model.fit(X_dev, y_dev)

print("\nModel trained successfully.")
print("C:", C_VALUE)
print("Threshold:", THRESHOLD)

# -----------------------------------
# 5. Evaluate independent test data
# -----------------------------------

probabilities = model.predict_proba(X_test)[:, 1]

predictions = (
    probabilities >= THRESHOLD
).astype(int)

accuracy = accuracy_score(y_test, predictions)
precision = precision_score(
    y_test, predictions, zero_division=0
)
recall = recall_score(
    y_test, predictions, zero_division=0
)
f1 = f1_score(
    y_test, predictions, zero_division=0
)
roc = roc_auc_score(y_test, probabilities)
pr = average_precision_score(y_test, probabilities)

# -----------------------------------
# 6. Display final results
# -----------------------------------

print("\n========== INDEPENDENT TEST RESULTS ==========")

print(f"Accuracy:  {accuracy * 100:.2f}%")
print(f"Precision: {precision * 100:.2f}%")
print(f"Fraud Recall: {recall * 100:.2f}%")
print(f"F1 Score:  {f1 * 100:.2f}%")
print(f"ROC-AUC:   {roc * 100:.2f}%")
print(f"PR-AUC:    {pr * 100:.2f}%")

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, predictions))

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        predictions,
        target_names=["Legitimate", "Fraud"],
        zero_division=0
    )
)

print("\n========== FROZEN CONFIGURATION ==========")
print("Algorithm: Logistic Regression")
print("C:", C_VALUE)
print("Threshold:", THRESHOLD)
print("Scaling: StandardScaler")
print("Random seed: 2026")

print("\nNo existing models were overwritten.")
print("========== VALIDATION COMPLETED ==========")
