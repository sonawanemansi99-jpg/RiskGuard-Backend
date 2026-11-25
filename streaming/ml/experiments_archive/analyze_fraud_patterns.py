
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(
    BASE_DIR, "data", "post_drift_transactions.csv"
)

df = pd.read_csv(DATA_PATH)

print("\n========== DATASET OVERVIEW ==========")
print("Total transactions:", len(df))
print("Fraud transactions:", int(df["is_fraud"].sum()))
print("Legitimate transactions:", int((df["is_fraud"] == 0).sum()))
print("Fraud percentage:", round(df["is_fraud"].mean() * 100, 2), "%")

def fraud_analysis(column):
    print(f"\n========== FRAUD RATE BY {column.upper()} ==========")

    result = (
        df.groupby(column, observed=True)["is_fraud"]
        .agg(["count", "sum", "mean"])
        .reset_index()
    )

    result["fraud_percentage"] = (result["mean"] * 100).round(2)

    result = result.rename(columns={
        "count": "total_transactions",
        "sum": "fraud_transactions"
    })

    print(
        result.drop(columns=["mean"])
        .to_string(index=False)
    )

# Categorical feature analysis
for column in [
    "new_device",
    "location",
    "merchant_category"
]:
    fraud_analysis(column)

# Transaction frequency analysis
df["transaction_frequency_group"] = pd.cut(
    df["transactions_last_hour"],
    bins=[-1, 1, 3, 5, 100000],
    labels=["0-1", "2-3", "4-5", "6+"]
)

fraud_analysis("transaction_frequency_group")

# Transaction amount analysis
df["amount_group"] = pd.qcut(
    df["amount"],
    q=5,
    duplicates="drop"
)

fraud_analysis("amount_group")

# Hour analysis
df["hour_group"] = pd.cut(
    df["hour"],
    bins=[-1, 5, 11, 17, 21, 23],
    labels=[
        "Late night (0-5)",
        "Morning (6-11)",
        "Afternoon (12-17)",
        "Evening (18-21)",
        "Night (22-23)"
    ]
)

fraud_analysis("hour_group")

# Feature statistics by actual fraud label
print("\n========== NUMERICAL FEATURES BY FRAUD LABEL ==========")

numeric_columns = [
    "amount",
    "hour",
    "new_device",
    "transactions_last_hour"
]

print(
    df.groupby("is_fraud")[numeric_columns]
    .mean()
    .round(2)
    .to_string()
)

print("\n========== ANALYSIS COMPLETED ==========")
