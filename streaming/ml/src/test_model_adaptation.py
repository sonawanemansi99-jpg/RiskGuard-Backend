
from pathlib import Path

import joblib
import pandas as pd

from sklearn.base import clone
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    classification_report
)

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = BASE_DIR / "data" / "post_drift_transactions.csv"
MODEL_PATH = BASE_DIR / "models" / "riskguard_model.pkl"
ADAPTED_PATH = BASE_DIR / "models" / "riskguard_adapted.pkl"

FEATURE_COLUMNS = [
    "amount",
    "hour",
    "location",
    "merchant_category",
    "new_device",
    "transactions_last_hour"
]

def evaluate(model, X, y):
    predictions = model.predict(X)

    return {
        "precision": precision_score(
            y, predictions, zero_division=0
        ),
        "recall": recall_score(
            y, predictions, zero_division=0
        ),
        "f1": f1_score(
            y, predictions, zero_division=0
        )
    }

def main():
    print("\nStarting post-drift adaptation experiment...")

    df = pd.read_csv(DATA_PATH)

    X = df[FEATURE_COLUMNS]
    y = df["is_fraud"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    current_model = joblib.load(MODEL_PATH)

    print("\nEvaluating original model on post-drift data...")
    original_metrics = evaluate(
        current_model, X_test, y_test
    )

    adapted_model = clone(current_model)

    print("\nTraining adapted model on new labeled data...")
    adapted_model.fit(X_train, y_train)

    adapted_metrics = evaluate(
        adapted_model, X_test, y_test
    )

    print("\n========== MODEL COMPARISON ==========")
    print("Original model:", original_metrics)
    print("Adapted model:", adapted_metrics)

    print("\nAdapted model classification report:")
    print(
        classification_report(
            y_test,
            adapted_model.predict(X_test),
            zero_division=0
        )
    )

    joblib.dump(adapted_model, ADAPTED_PATH)

    print("\nAdapted model saved to:", ADAPTED_PATH)
    print("Active model remains unchanged.")

if __name__ == "__main__":
    main()
