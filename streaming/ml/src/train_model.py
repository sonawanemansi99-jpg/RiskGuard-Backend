
import pandas as pd
import joblib

from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)


# Project paths
BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = BASE_DIR / "data" / "bank_transactions.csv"
MODEL_PATH = BASE_DIR / "models" / "riskguard_model.pkl"


def train_model():

    print("\nLoading banking transaction dataset...")

    df = pd.read_csv(DATA_PATH)

    print("Dataset shape:", df.shape)

    # Input features
    feature_columns = [
        "amount",
        "hour",
        "location",
        "merchant_category",
        "new_device",
        "transactions_last_hour"
    ]

    X = df[feature_columns]

    # Target: 0 = Legitimate, 1 = Fraud
    y = df["is_fraud"]

    # Numerical and categorical features
    numeric_features = [
        "amount",
        "hour",
        "new_device",
        "transactions_last_hour"
    ]

    categorical_features = [
        "location",
        "merchant_category"
    ]

    # Convert categorical features into numbers
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", "passthrough", numeric_features),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_features
            )
        ]
    )

    # Random Forest model
    classifier = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        n_jobs=-1
    )

    # Complete ML pipeline
    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier)
        ]
    )

    # Split dataset into training and testing
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    print("\nTraining samples:", len(X_train))
    print("Testing samples:", len(X_test))

    print("\nTraining Random Forest model...")

    model.fit(X_train, y_train)

    print("Model training completed!")

    # Predict on test data
    predictions = model.predict(X_test)

    # Evaluate performance
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

    print("\n========== MODEL PERFORMANCE ==========")

    print(f"Accuracy : {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall   : {recall:.4f}")
    print(f"F1 Score : {f1:.4f}")

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, predictions))

    print("\nClassification Report:")
    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0
        )
    )

    # Save the complete pipeline
    MODEL_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    joblib.dump(model, MODEL_PATH)

    print("\nModel saved successfully!")
    print("Model location:", MODEL_PATH)


if __name__ == "__main__":
    train_model()
