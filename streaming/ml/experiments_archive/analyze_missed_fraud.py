
import os
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix

# Project paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(
    BASE_DIR, "data", "post_drift_transactions.csv"
)

MODEL_PATH = os.path.join(
    BASE_DIR, "models", "riskguard_improved_candidate.pkl"
)

# Load dataset and model
df = pd.read_csv(DATA_PATH)
model = joblib.load(MODEL_PATH)

# Separate features and target
X = df.drop(columns=["is_fraud", "transaction_ref"], errors="ignore")
y = df["is_fraud"]

# Recreate the same 80:20 test split
X_dev, X_test, y_dev, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

# Predict fraud probabilities
probabilities = model.predict_proba(X_test)[:, 1]

threshold = getattr(model, "risk_threshold_", 0.56)
predictions = (probabilities >= threshold).astype(int)

# Confusion matrix
tn, fp, fn, tp = confusion_matrix(
    y_test, predictions, labels=[0, 1]
).ravel()

print("\n========== MODEL ERROR ANALYSIS ==========")
print("Threshold:", threshold)
print("True Negatives:", tn)
print("False Positives:", fp)
print("False Negatives:", fn)
print("True Positives:", tp)

# Identify missed fraud
results = X_test.copy()
results["actual_fraud"] = y_test
results["predicted_fraud"] = predictions
results["fraud_probability"] = probabilities

missed_fraud = results[
    (results["actual_fraud"] == 1) &
    (results["predicted_fraud"] == 0)
]

false_alarms = results[
    (results["actual_fraud"] == 0) &
    (results["predicted_fraud"] == 1)
]

print("\n========== MISSED FRAUD TRANSACTIONS ==========")
print("Total missed:", len(missed_fraud))
print(missed_fraud.head(25).to_string(index=False))

print("\n========== FALSE ALARMS ==========")
print("Total false alarms:", len(false_alarms))
print(false_alarms.head(25).to_string(index=False))

print("\n========== MISSED FRAUD FEATURE ANALYSIS ==========")

if len(missed_fraud) > 0:
    print(
        missed_fraud.select_dtypes(include="number")
        .drop(columns=["actual_fraud", "predicted_fraud"],
              errors="ignore")
        .mean()
        .round(2)
    )

print("\n========== COMPLETE ==========")
