
import pandas as pd
import joblib

from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = BASE_DIR / "data" / "bank_transactions.csv"
MODEL_DIR = BASE_DIR / "models"

df = pd.read_csv(DATA_PATH)

features = [
    "amount",
    "hour",
    "location",
    "merchant_category",
    "new_device",
    "transactions_last_hour"
]

X = df[features]
y = df["is_fraud"]

_, X_test, _, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

models = {
    "Random Forest": MODEL_DIR / "riskguard_model.pkl",
    "Ensemble": MODEL_DIR / "riskguard_ensemble.pkl"
}

for name, path in models.items():

    model = joblib.load(path)
    predictions = model.predict(X_test)

    print(f"\n========== {name} ==========")

    print("Accuracy :", round(accuracy_score(y_test, predictions), 4))
    print("Precision:", round(precision_score(y_test, predictions, zero_division=0), 4))
    print("Recall   :", round(recall_score(y_test, predictions, zero_division=0), 4))
    print("F1 Score :", round(f1_score(y_test, predictions, zero_division=0), 4))
