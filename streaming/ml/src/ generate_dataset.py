
import numpy as np
import pandas as pd
from pathlib import Path

# Reproducible synthetic data
rng = np.random.default_rng(42)

NUM_TRANSACTIONS = 10_000

LOCATIONS = ["Pune", "Mumbai", "Nashik", "Delhi", "Bengaluru"]
MERCHANT_CATEGORIES = [
    "Retail",
    "Grocery",
    "Travel",
    "Electronics",
    "Restaurant",
    "Online",
]

records = []

for i in range(NUM_TRANSACTIONS):
    # Generate transaction characteristics
    amount = round(float(rng.lognormal(mean=7.5, sigma=1.0)), 2)
    amount = min(amount, 200_000.00)

    hour = int(rng.integers(0, 24))
    location = str(rng.choice(LOCATIONS))
    merchant_category = str(rng.choice(MERCHANT_CATEGORIES))

    # Synthetic indicators representing available context
    new_device = int(rng.choice([0, 1], p=[0.80, 0.20]))
    transactions_last_hour = int(
        rng.poisson(lam=1.5)
    )

    # Construct a risk tendency for the simulator.
    # These rules generate synthetic labels, not real fraud evidence.
    risk_points = 0

    if amount > 50_000:
        risk_points += 2
    elif amount > 20_000:
        risk_points += 1

    if hour <= 5:
        risk_points += 2
    elif hour >= 23:
        risk_points += 1

    if new_device == 1:
        risk_points += 1

    if location == "Mumbai" and merchant_category == "Online":
        risk_points += 1

    if transactions_last_hour >= 5:
        risk_points += 2
    elif transactions_last_hour >= 3:
        risk_points += 1

    # Convert the risk tendency into a probability.
    # Randomness prevents every record with the same pattern
    # from automatically receiving the same label.
    fraud_probability = 1 / (
        1 + np.exp(-(risk_points - 3) * 0.9)
    )

    is_fraud = int(rng.binomial(1, fraud_probability))

    records.append({
        "transaction_ref": f"TRAIN_{i + 1:06d}",
        "amount": amount,
        "hour": hour,
        "location": location,
        "merchant_category": merchant_category,
        "new_device": new_device,
        "transactions_last_hour": transactions_last_hour,
        "is_fraud": is_fraud,
    })

df = pd.DataFrame(records)

# Save the dataset inside streaming/ml/data/
output_path = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "bank_transactions.csv"
)

output_path.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(output_path, index=False)

print("\nSynthetic dataset created successfully!")
print(f"File: {output_path}")
print(f"Total transactions: {len(df)}")

print("\nFirst 5 transactions:")
print(df.head().to_string(index=False))

print("\nFraud label distribution:")
print(
    df["is_fraud"]
    .value_counts()
    .rename(index={0: "Legitimate", 1: "Fraud"})
    .to_string()
)

print("\nFraud percentage:")
print(f"{df['is_fraud'].mean() * 100:.2f}%")
