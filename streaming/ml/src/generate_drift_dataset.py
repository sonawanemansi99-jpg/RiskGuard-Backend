
from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "bank_transactions.csv"
OUTPUT_PATH = BASE_DIR / "data" / "post_drift_transactions.csv"

rng = np.random.default_rng(123)

# Load the original dataset's feature structure
df = pd.read_csv(DATA_PATH)

# Generate new independent feature values
n = 10000

new_data = pd.DataFrame({
    "transaction_ref": [f"DRIFT_{i:06d}" for i in range(n)],
    "amount": np.minimum(
        rng.lognormal(8.5, 1.1, n),
        200000
    ).round(2),
    "hour": rng.integers(0, 24, n),
    "location": rng.choice(
        ["Pune", "Mumbai", "Nashik", "Delhi", "Bengaluru"], n
    ),
    "merchant_category": rng.choice(
        ["Retail", "Grocery", "Travel", "Electronics",
         "Restaurant", "Online"], n
    ),
    "new_device": rng.binomial(1, 0.4, n),
    "transactions_last_hour": rng.poisson(3, n),
})

# New synthetic fraud behavior
# More dependent on device and transaction frequency
risk = (
    -4.0
    + 2.0 * new_data["new_device"]
    + 0.6 * new_data["transactions_last_hour"]
    + 0.000015 * new_data["amount"]
)

probability = 1 / (1 + np.exp(-risk))

new_data["is_fraud"] = rng.binomial(
    1, probability
)

new_data.to_csv(OUTPUT_PATH, index=False)

print("Post-drift dataset generated successfully!")
print("Dataset shape:", new_data.shape)
print("Fraud percentage:",
      round(new_data["is_fraud"].mean() * 100, 2))
print("Saved to:", OUTPUT_PATH)
