import joblib
import pandas as pd

from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix
)

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = BASE_DIR / "data" / "post_drift_transactions.csv"
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
    "Random Forest": {
        "path": MODEL_DIR / "riskguard_model.pkl",
        "features": features,
        "threshold": 0.50
    },
    "Balanced Ensemble": {
        "path": MODEL_DIR / "riskguard_ensemble.pkl",
        "features": features,
        "threshold": 0.50
    },
    "Validated Logistic Regression": {
        "path": MODEL_DIR / "riskguard_logistic_validated.pkl",
        "features": [
            "amount",
            "new_device",
            "transactions_last_hour"
        ],
        "threshold": 0.40
    }
}

results = []

print("\n========== FINAL FAIR MODEL COMPARISON ==========")
print("Dataset: Post-drift transactions")
print("Test records:", len(X_test))
print("Same test split for all three models")

for name, config in models.items():

    path = config["path"]

    if not path.exists():
        print(f"\n{name}: MODEL FILE NOT FOUND")
        continue

    model = joblib.load(path)

    model_features = X_test[config["features"]]

    probabilities = model.predict_proba(model_features)[:, 1]

    predictions = (
        probabilities >= config["threshold"]
    ).astype(int)

    accuracy = accuracy_score(y_test, predictions)
    precision = precision_score(y_test, predictions, zero_division=0)
    recall = recall_score(y_test, predictions, zero_division=0)
    f1 = f1_score(y_test, predictions, zero_division=0)
    auc = roc_auc_score(y_test, probabilities)

    results.append({
        "Model": name,
        "Accuracy": accuracy * 100,
        "Precision": precision * 100,
        "Recall": recall * 100,
        "F1 Score": f1 * 100,
        "ROC-AUC": auc * 100
    })

    print(f"\n========== {name.upper()} ==========")
    print(f"Threshold : {config['threshold']}")
    print(f"Accuracy  : {accuracy * 100:.2f}%")
    print(f"Precision : {precision * 100:.2f}%")
    print(f"Recall    : {recall * 100:.2f}%")
    print(f"F1 Score  : {f1 * 100:.2f}%")
    print(f"ROC-AUC   : {auc * 100:.2f}%")
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, predictions))

if results:
    result_df = pd.DataFrame(results).set_index("Model")

    print("\n========== FINAL SUMMARY ==========")
    print(result_df.round(2).to_string())

    best = result_df["Accuracy"].idxmax()
    print(f"\nHighest measured accuracy: {best}")
    print(f"Accuracy: {result_df.loc[best, 'Accuracy']:.2f}%")
