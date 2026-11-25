
import os
import joblib
import numpy as np
import pandas as pd

from sklearn.base import clone
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
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

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(
    BASE_DIR, "data", "post_drift_transactions.csv"
)

GB_PATH = os.path.join(
    BASE_DIR, "models", "riskguard_improved_candidate.pkl"
)

df = pd.read_csv(DATA_PATH)

X = df.drop(
    columns=["is_fraud", "transaction_ref"],
    errors="ignore"
)
y = df["is_fraud"]

# Fresh common split for all models
X_dev, X_test, y_dev, y_test = train_test_split(
    X, y,
    test_size=0.20,
    random_state=31415,
    stratify=y
)

X_train, X_val, y_train, y_val = train_test_split(
    X_dev, y_dev,
    test_size=0.25,
    random_state=31415,
    stratify=y_dev
)

# Load existing Gradient Boosting pipeline as an experiment template
gb_template = joblib.load(GB_PATH)

# Tune Logistic Regression regularization
C_VALUES = [0.01, 0.1, 1, 10, 100, 1000]

best_lr = None
best_lr_f1 = -1
best_lr_c = None
best_lr_threshold = None

print("\n========== LOGISTIC REGRESSION TUNING ==========")

for c_value in C_VALUES:

    model = clone(gb_template)

    # Replace only the classifier; retain preprocessing
    model.set_params(
        classifier=LogisticRegression(
            C=c_value,
            max_iter=5000,
            random_state=42
        )
    )

    model.fit(X_train, y_train)

    val_prob = model.predict_proba(X_val)[:, 1]

    for threshold in np.arange(0.10, 0.91, 0.01):

        val_pred = (val_prob >= threshold).astype(int)

        score = f1_score(
            y_val,
            val_pred,
            zero_division=0
        )

        if score > best_lr_f1:
            best_lr_f1 = score
            best_lr = clone(model)
            best_lr_c = c_value
            best_lr_threshold = threshold

    print(
        f"C={c_value:<7} "
        f"Best F1 so far={best_lr_f1 * 100:.2f}%"
    )

# Train selected Logistic Regression on full development data
best_lr.fit(X_dev, y_dev)

# Train Gradient Boosting on the same development data
gb_model = clone(gb_template)
gb_model.fit(X_dev, y_dev)

# Evaluate both models on the same untouched test set
models = {
    "Logistic Regression": (best_lr, best_lr_threshold),
    "Gradient Boosting": (gb_model, 0.56)
}

print("\n========== FINAL COMPARISON ==========")
print("Fresh test set:", len(X_test))
print("Selected Logistic C:", best_lr_c)

for name, (model, threshold) in models.items():

    probabilities = model.predict_proba(X_test)[:, 1]
    predictions = (probabilities >= threshold).astype(int)

    print(f"\n========== {name} ==========")
    print("Threshold:", round(threshold, 2))

    print("Accuracy:",
          round(accuracy_score(y_test, predictions) * 100, 2), "%")

    print("Precision:",
          round(precision_score(y_test, predictions, zero_division=0) * 100, 2), "%")

    print("Fraud Recall:",
          round(recall_score(y_test, predictions, zero_division=0) * 100, 2), "%")

    print("F1 Score:",
          round(f1_score(y_test, predictions, zero_division=0) * 100, 2), "%")

    print("ROC-AUC:",
          round(roc_auc_score(y_test, probabilities) * 100, 2), "%")

    print("PR-AUC:",
          round(average_precision_score(y_test, probabilities) * 100, 2), "%")

    print("Confusion Matrix:")
    print(confusion_matrix(y_test, predictions))

print("\n========== EXPERIMENT COMPLETED ==========")
print("No existing model files were overwritten.")
