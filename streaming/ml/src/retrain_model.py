
from pathlib import Path

import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    classification_report
)

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = BASE_DIR / "data" / "bank_transactions.csv"

CURRENT_MODEL_PATH = (
    BASE_DIR / "models" / "riskguard_model.pkl"
)

CANDIDATE_MODEL_PATH = (
    BASE_DIR / "models" / "riskguard_candidate.pkl"
)

FEATURE_COLUMNS = [
    "amount",
    "hour",
    "location",
    "merchant_category",
    "new_device",
    "transactions_last_hour",
]


def evaluate_model(model, X, y):
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
    print("\nStarting RiskGuard Model Adaptation...")

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    if not CURRENT_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Current model not found: {CURRENT_MODEL_PATH}"
        )

    df = pd.read_csv(DATA_PATH)

    X = df[FEATURE_COLUMNS]
    y = df["is_fraud"]

    # Use a separate holdout for comparison.
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=123,
        stratify=y
    )

    print("Loading existing ML model...")

    current_model = joblib.load(
        CURRENT_MODEL_PATH
    )

    # Train a separate candidate model.
    # Do not modify the active model in place.
    from sklearn.base import clone

    candidate_model = clone(current_model)

    print("Training candidate model...")

    candidate_model.fit(X_train, y_train)

    print("Evaluating existing model...")

    current_metrics = evaluate_model(
        current_model, X_test, y_test
    )

    print("Evaluating candidate model...")

    candidate_metrics = evaluate_model(
        candidate_model, X_test, y_test
    )

    print("\n========== MODEL COMPARISON ==========")

    print("Current model:", current_metrics)
    print("Candidate model:", candidate_metrics)

    # Save for inspection; do not activate automatically.
    joblib.dump(
        candidate_model,
        CANDIDATE_MODEL_PATH
    )

    print("\nCandidate model saved:")
    print(CANDIDATE_MODEL_PATH)

    if (
        candidate_metrics["f1"] > current_metrics["f1"]
        and candidate_metrics["recall"] >= current_metrics["recall"]
    ):
        print(
            "\nCandidate passed the preliminary "
            "metric comparison."
        )
    else:
        print(
            "\nCandidate did not improve the "
            "required metrics."
        )

    print(
        "\nNo model was automatically activated."
    )


if __name__ == "__main__":
    main()
