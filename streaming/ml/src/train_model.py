
import pandas as pd
import joblib

from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)


# ==========================================
# 1. PROJECT PATHS
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = BASE_DIR / "data" / "bank_transactions.csv"

MODEL_PATH = BASE_DIR / "models" / "riskguard_ensemble.pkl"


# ==========================================
# 2. TRAIN ENSEMBLE CLASSIFIER
# ==========================================

def train_model():

    print("\nLoading banking transaction dataset...")

    df = pd.read_csv(DATA_PATH)

    print("Dataset shape:", df.shape)

    # ======================================
    # INPUT FEATURES
    # ======================================

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

    # ======================================
    # NUMERICAL & CATEGORICAL FEATURES
    # ======================================

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

    # ======================================
    # DATA PREPROCESSING
    # ======================================

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                StandardScaler(),
                numeric_features
            ),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_features
            )
        ]
    )

    # ======================================
    # RANDOM FOREST CLASSIFIER
    # ======================================

    random_forest = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1
    )

    # ======================================
    # LOGISTIC REGRESSION CLASSIFIER
    # ======================================

    logistic_regression = LogisticRegression(
        max_iter=1000,
        random_state=42,
        class_weight="balanced"
    )

    # ======================================
    # SOFT VOTING ENSEMBLE CLASSIFIER
    # ======================================

    ensemble_classifier = VotingClassifier(
        estimators=[
            ("random_forest", random_forest),
            ("logistic_regression", logistic_regression)
        ],
        voting="soft"
    )

    # ======================================
    # COMPLETE MACHINE LEARNING PIPELINE
    # ======================================

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", ensemble_classifier)
        ]
    )

    # ======================================
    # SPLIT DATASET
    # ======================================

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    print("\nTraining samples:", len(X_train))
    print("Testing samples:", len(X_test))

    # ======================================
    # TRAIN MODEL
    # ======================================

    print("\nTraining Balanced Ensemble Classifier...")
    print("Models: Random Forest + Logistic Regression")

    model.fit(X_train, y_train)

    print("\nEnsemble training completed!")

    # ======================================
    # MODEL PREDICTIONS
    # ======================================

    predictions = model.predict(X_test)

    # ======================================
    # MODEL EVALUATION
    # ======================================

    accuracy = accuracy_score(y_test, predictions)

    precision = precision_score(
        y_test,
        predictions,
        zero_division=0
    )

    recall = recall_score(
        y_test,
        predictions,
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        predictions,
        zero_division=0
    )

    print("\n========== ENSEMBLE PERFORMANCE ==========")

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

    # ======================================
    # SAVE ENSEMBLE MODEL
    # ======================================

    MODEL_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    joblib.dump(model, MODEL_PATH)

    print("\nEnsemble model saved successfully!")
    print("Model location:", MODEL_PATH)


if __name__ == "__main__":
    train_model()
