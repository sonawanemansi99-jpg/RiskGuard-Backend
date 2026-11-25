
import os
import joblib
import numpy as np
import pandas as pd

from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    RandomForestClassifier,
    ExtraTreesClassifier,
    GradientBoostingClassifier
)
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.utils.class_weight import compute_sample_weight


# --------------------------------------------------
# 1. Load post-drift dataset
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(
    BASE_DIR, "data", "post_drift_transactions.csv"
)

MODEL_DIR = os.path.join(BASE_DIR, "models")
OUTPUT_PATH = os.path.join(
    MODEL_DIR, "riskguard_improved_candidate.pkl"
)

os.makedirs(MODEL_DIR, exist_ok=True)

df = pd.read_csv(DATA_PATH)

FEATURES = [
    "amount",
    "hour",
    "location",
    "merchant_category",
    "new_device",
    "transactions_last_hour",
]

X = df[FEATURES]
y = df["is_fraud"]

print("\n========== DATASET INFORMATION ==========")
print("Total transactions:", len(df))
print("Fraud transactions:", int(y.sum()))
print("Legitimate transactions:", int((y == 0).sum()))


# --------------------------------------------------
# 2. Split into training, validation and test sets
# --------------------------------------------------

# Keep the same 20% holdout split used in the
# previous adaptation experiment.

X_dev, X_test, y_dev, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

# Divide the remaining 80% into 60% training
# and 20% validation.

X_train, X_val, y_train, y_val = train_test_split(
    X_dev,
    y_dev,
    test_size=0.25,
    random_state=42,
    stratify=y_dev
)

print("\n========== DATA SPLIT ==========")
print("Training records:", len(X_train))
print("Validation records:", len(X_val))
print("Reserved test records:", len(X_test))


# --------------------------------------------------
# 3. Preprocessing
# --------------------------------------------------

numeric_features = [
    "amount",
    "hour",
    "new_device",
    "transactions_last_hour",
]

categorical_features = [
    "location",
    "merchant_category",
]

def create_pipeline(classifier):

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", "passthrough", numeric_features),
            (
                "categorical",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False
                ),
                categorical_features
            ),
        ]
    )

    return Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", classifier),
    ])


# --------------------------------------------------
# 4. Define candidate models
# --------------------------------------------------

models = {

    "Random Forest Balanced": RandomForestClassifier(
        n_estimators=300,
        min_samples_split=5,
        min_samples_leaf=2,
        max_features="sqrt",
        class_weight="balanced_subsample",
        n_jobs=-1,
        random_state=42
    ),

    "Random Forest Limited Depth": RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        min_samples_split=8,
        min_samples_leaf=3,
        max_features="sqrt",
        class_weight="balanced_subsample",
        n_jobs=-1,
        random_state=42
    ),

    "Extra Trees Balanced": ExtraTreesClassifier(
        n_estimators=300,
        min_samples_split=5,
        min_samples_leaf=2,
        max_features="sqrt",
        class_weight="balanced",
        n_jobs=-1,
        random_state=42
    ),

    "Gradient Boosting": GradientBoostingClassifier(
        n_estimators=150,
        learning_rate=0.05,
        max_depth=2,
        min_samples_leaf=5,
        random_state=42
    ),
}


# --------------------------------------------------
# 5. Train and compare using validation data
# --------------------------------------------------

results = []
trained_models = {}

print("\n========== MODEL EXPERIMENTS ==========")

for name, classifier in models.items():

    print(f"\nTraining: {name}")

    model = create_pipeline(classifier)

    if name == "Gradient Boosting":

        sample_weights = compute_sample_weight(
            class_weight="balanced",
            y=y_train
        )

        model.fit(
            X_train,
            y_train,
            classifier__sample_weight=sample_weights
        )

    else:
        model.fit(X_train, y_train)

    probabilities = model.predict_proba(X_val)[:, 1]

    # Evaluate using the standard 0.50 threshold.

    default_predictions = (
        probabilities >= 0.50
    ).astype(int)

    default_f1 = f1_score(
        y_val,
        default_predictions,
        zero_division=0
    )

    # Find the threshold giving the highest
    # validation F1 score.

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
            best_threshold = float(threshold)

    best_predictions = (
        probabilities >= best_threshold
    ).astype(int)

    precision = precision_score(
        y_val,
        best_predictions,
        zero_division=0
    )

    recall = recall_score(
        y_val,
        best_predictions,
        zero_division=0
    )

    accuracy = accuracy_score(
        y_val,
        best_predictions
    )

    roc_auc = roc_auc_score(
        y_val,
        probabilities
    )

    pr_auc = average_precision_score(
        y_val,
        probabilities
    )

    results.append({
        "Model": name,
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1 Score": best_f1,
        "ROC-AUC": roc_auc,
        "PR-AUC": pr_auc,
        "Threshold": best_threshold,
        "Default F1": default_f1,
    })

    trained_models[name] = model

    print("Default threshold F1:", round(default_f1, 4))
    print("Best threshold:", round(best_threshold, 2))
    print("Validation precision:", round(precision, 4))
    print("Validation recall:", round(recall, 4))
    print("Validation F1:", round(best_f1, 4))
    print("Validation ROC-AUC:", round(roc_auc, 4))
    print("Validation PR-AUC:", round(pr_auc, 4))


# --------------------------------------------------
# 6. Select the best candidate using validation F1
# --------------------------------------------------

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    by="F1 Score",
    ascending=False
)

print("\n========== VALIDATION COMPARISON ==========")
print(results_df.to_string(index=False))

best_name = results_df.iloc[0]["Model"]
best_threshold = float(
    results_df.iloc[0]["Threshold"]
)

print("\nSelected model:", best_name)
print("Selected threshold:", round(best_threshold, 2))


# --------------------------------------------------
# 7. Retrain selected model on all development data
# --------------------------------------------------

print("\nRetraining selected model on 80% development data...")

final_model = clone(
    create_pipeline(models[best_name])
)

if best_name == "Gradient Boosting":

    final_weights = compute_sample_weight(
        class_weight="balanced",
        y=y_dev
    )

    final_model.fit(
        X_dev,
        y_dev,
        classifier__sample_weight=final_weights
    )

else:
    final_model.fit(X_dev, y_dev)


# --------------------------------------------------
# 8. Evaluate once on the reserved test set
# --------------------------------------------------

print("\n========== FINAL UNSEEN TEST RESULTS ==========")

test_probabilities = final_model.predict_proba(X_test)[:, 1]

test_predictions = (
    test_probabilities >= best_threshold
).astype(int)

print("Accuracy:",
      round(accuracy_score(y_test, test_predictions), 4))

print("Precision:",
      round(precision_score(
          y_test, test_predictions, zero_division=0
      ), 4))

print("Fraud Recall:",
      round(recall_score(
          y_test, test_predictions, zero_division=0
      ), 4))

print("F1 Score:",
      round(f1_score(
          y_test, test_predictions, zero_division=0
      ), 4))

print("ROC-AUC:",
      round(roc_auc_score(y_test, test_probabilities), 4))

print("PR-AUC:",
      round(average_precision_score(
          y_test, test_probabilities
      ), 4))


# --------------------------------------------------
# 9. Save the improved candidate separately
# --------------------------------------------------

# Keep the selected threshold with the candidate model.
final_model.risk_threshold_ = best_threshold

joblib.dump(final_model, OUTPUT_PATH)

print("\n========== EXPERIMENT COMPLETED ==========")
print("Selected model:", best_name)
print("Candidate saved at:")
print(OUTPUT_PATH)

print("\nExisting active model was not modified.")
