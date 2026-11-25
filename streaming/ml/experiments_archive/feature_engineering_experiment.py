
import os
import numpy as np
import pandas as pd
import joblib

from sklearn.base import clone
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
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

GB_PATH = os.path.join(
    BASE_DIR, "models", "riskguard_improved_candidate.pkl"
)

df = pd.read_csv(DATA_PATH)

y = df["is_fraud"]

# ----------------------------------
# 1. Feature Engineering
# ----------------------------------

def create_features(data):

    data = data.copy()

    data["amount_log"] = np.log1p(data["amount"])

    data["amount_per_transaction"] = (
        data["amount"] /
        (data["transactions_last_hour"] + 1)
    )

    data["amount_velocity"] = (
        data["amount"] *
        data["transactions_last_hour"]
    )

    data["device_frequency_risk"] = (
        data["new_device"] *
        data["transactions_last_hour"]
    )

    data["high_velocity"] = (
        data["transactions_last_hour"] >= 5
    ).astype(int)

    data["new_device_high_velocity"] = (
        (data["new_device"] == 1) &
        (data["transactions_last_hour"] >= 4)
    ).astype(int)

    return data


X = df.drop(
    columns=["is_fraud", "transaction_ref"],
    errors="ignore"
)

X = create_features(X)

numeric_columns = X.select_dtypes(
    include=["number"]
).columns.tolist()

categorical_columns = X.select_dtypes(
    exclude=["number"]
).columns.tolist()

# ----------------------------------
# 2. Train / Validation / Test Split
# ----------------------------------

X_dev, X_test, y_dev, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=31415,
    stratify=y
)

X_train, X_val, y_train, y_val = train_test_split(
    X_dev,
    y_dev,
    test_size=0.25,
    random_state=31415,
    stratify=y_dev
)

# ----------------------------------
# 3. Load Existing GB Configuration
# ----------------------------------

gb_template = joblib.load(GB_PATH)

# Reuse only the Gradient Boosting classifier settings.
gb_classifier = clone(
    gb_template.named_steps["classifier"]
)

# ----------------------------------
# 4. Build Correct Preprocessors
# ----------------------------------

def create_preprocessor(scale_numeric=False):

    numeric_steps = [
        ("imputer", SimpleImputer(strategy="median"))
    ]

    if scale_numeric:
        numeric_steps.append(
            ("scaler", StandardScaler())
        )

    numeric_pipeline = Pipeline(numeric_steps)

    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore"))
    ])

    return ColumnTransformer([
        ("numeric", numeric_pipeline, numeric_columns),
        ("categorical", categorical_pipeline, categorical_columns)
    ])


# Gradient Boosting does not require numeric scaling.
gb_preprocessor = create_preprocessor(
    scale_numeric=False
)

# Logistic Regression benefits from numeric scaling.
lr_preprocessor = create_preprocessor(
    scale_numeric=True
)

# ----------------------------------
# 5. Build Models
# ----------------------------------

gb_model = Pipeline([
    ("preprocessor", gb_preprocessor),
    ("classifier", gb_classifier)
])

lr_model = Pipeline([
    ("preprocessor", lr_preprocessor),
    ("classifier", LogisticRegression(
        C=0.1,
        max_iter=5000,
        random_state=42
    ))
])

# ----------------------------------
# 6. Threshold Tuning
# ----------------------------------

def tune_threshold(model):

    probabilities = model.predict_proba(X_val)[:, 1]

    best_threshold = 0.50
    best_f1 = -1

    for threshold in np.arange(0.10, 0.91, 0.01):

        predictions = (
            probabilities >= threshold
        ).astype(int)

        score = f1_score(
            y_val,
            predictions,
            zero_division=0
        )

        if score > best_f1:
            best_f1 = score
            best_threshold = threshold

    return best_threshold, best_f1


# ----------------------------------
# 7. Train and Evaluate
# ----------------------------------

models = {
    "Feature Engineered Logistic Regression": lr_model,
    "Feature Engineered Gradient Boosting": gb_model
}

results = []

print("\n========== FEATURE ENGINEERING EXPERIMENT ==========")

for name, model in models.items():

    print("\nTraining:", name)

    model.fit(X_train, y_train)

    threshold, validation_f1 = tune_threshold(model)

    print(
        "Validation F1:",
        round(validation_f1 * 100, 2),
        "%"
    )

    print("Selected threshold:", round(threshold, 2))

    # Refit using complete development data
    model.fit(X_dev, y_dev)

    probabilities = model.predict_proba(X_test)[:, 1]

    predictions = (
        probabilities >= threshold
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

    print("\nFinal Test Results:")
    print("Accuracy:", round(accuracy * 100, 2), "%")
    print("Precision:", round(precision * 100, 2), "%")
    print("Fraud Recall:", round(recall * 100, 2), "%")
    print("F1 Score:", round(f1 * 100, 2), "%")
    print("ROC-AUC:", round(roc * 100, 2), "%")
    print("PR-AUC:", round(pr * 100, 2), "%")

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, predictions))

    results.append({
        "Model": name,
        "Accuracy": round(accuracy * 100, 2),
        "Precision": round(precision * 100, 2),
        "Recall": round(recall * 100, 2),
        "F1": round(f1 * 100, 2),
        "ROC-AUC": round(roc * 100, 2),
        "PR-AUC": round(pr * 100, 2),
        "Threshold": round(threshold, 2)
    })


# ----------------------------------
# 8. Final Comparison
# ----------------------------------

print("\n========== FINAL MODEL COMPARISON ==========")

result_df = pd.DataFrame(results)

print(result_df.to_string(index=False))

print("\n========== EXPERIMENT COMPLETED ==========")
print("No existing models were overwritten.")
