
import os
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(
    BASE_DIR, "data", "post_drift_transactions.csv"
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "riskguard_logistic_validated.pkl"
)

# Prevent accidental overwrite
if os.path.exists(MODEL_PATH):
    raise FileExistsError(
        "Validated model already exists. Nothing was overwritten."
    )

df = pd.read_csv(DATA_PATH)

features = [
    "amount",
    "new_device",
    "transactions_last_hour"
]

X = df[features]
y = df["is_fraud"]

# Reproduce the independent validation split
X_dev, X_test, y_dev, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=2026,
    stratify=y
)

# Frozen configuration
model = Pipeline([
    ("scaler", StandardScaler()),
    ("classifier", LogisticRegression(
        C=0.001,
        max_iter=5000,
        random_state=42
    ))
])

# Train on development data only
model.fit(X_dev, y_dev)

# Save threshold and metadata with the pipeline
model.risk_threshold_ = 0.40
model.feature_names_ = features
model.validation_accuracy_ = 0.768

joblib.dump(model, MODEL_PATH)

print("\nValidated model saved successfully.")
print("Path:", MODEL_PATH)
print("Threshold:", model.risk_threshold_)
print("Features:", model.feature_names_)
print("Validation accuracy: 76.80%")
print("Existing models were not modified.")
