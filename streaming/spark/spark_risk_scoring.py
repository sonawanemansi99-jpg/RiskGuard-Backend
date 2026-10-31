
from pathlib import Path

import joblib
import pandas as pd

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType,
)

from drift_detector import RiskGuardDriftDetector
from mysql_writer import save_risk_batch


# ==========================================
# 1. CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_PATH = (
    BASE_DIR / "ml" / "models" / "riskguard_model.pkl"
)

KAFKA_SERVER = "localhost:9092"
KAFKA_TOPIC = "bank_transactions"

CHECKPOINT_PATH = (
    Path(__file__).resolve().parent
    / "checkpoints"
    / "risk_scoring"
)


# ==========================================
# 2. LOAD ML MODEL
# ==========================================

print("Loading RiskGuard ML model...")

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"ML model not found: {MODEL_PATH}"
    )

model = joblib.load(MODEL_PATH)

print("ML model loaded successfully!")


# ==========================================
# 3. INITIALIZE DRIFT DETECTOR
# ==========================================

drift_detector = RiskGuardDriftDetector()

print("ADWIN drift detector initialized!")


# ==========================================
# 4. ML FEATURES
# ==========================================

FEATURE_COLUMNS = [
    "amount",
    "hour",
    "location",
    "merchant_category",
    "new_device",
    "transactions_last_hour",
]


# ==========================================
# 5. KAFKA TRANSACTION SCHEMA
# ==========================================

transaction_schema = StructType([
    StructField("transaction_ref", StringType(), True),
    StructField("customer_ref", StringType(), True),
    StructField("amount", DoubleType(), True),
    StructField("currency", StringType(), True),
    StructField("location", StringType(), True),
    StructField("device_id", StringType(), True),
    StructField("merchant_category", StringType(), True),
    StructField("transaction_time", StringType(), True),
])


# ==========================================
# 6. RISK CLASSIFICATION
# ==========================================

def classify_risk(score):

    if score <= 30:
        return "LOW"

    elif score <= 70:
        return "MEDIUM"

    else:
        return "HIGH"


# ==========================================
# 7. PROCESS SPARK BATCH
# ==========================================

def score_batch(batch_df, batch_id):

    if batch_df.isEmpty():
        return

    print(f"\nProcessing Spark Batch: {batch_id}")

    # Convert Spark batch into Pandas DataFrame
    pdf = batch_df.toPandas()

    # Validate required fields
    pdf = pdf.dropna(
        subset=[
            "transaction_ref",
            "customer_ref",
            "amount",
            "location",
            "merchant_category",
            "transaction_time",
        ]
    ).copy()

    # Convert transaction timestamp
    pdf["transaction_time"] = pd.to_datetime(
        pdf["transaction_time"],
        errors="coerce",
        utc=True,
    )

    pdf = pdf.dropna(
        subset=["transaction_time"]
    )

    # Remove invalid amounts
    pdf = pdf[
        pdf["amount"] > 0
    ].copy()

    if pdf.empty:
        print(
            f"Batch {batch_id}: "
            "No valid transactions found."
        )
        return

    # ======================================
    # FEATURE ENGINEERING
    # ======================================

    print("Performing feature engineering...")

    pdf["hour"] = (
        pdf["transaction_time"].dt.hour
    )

    # Temporary feature defaults
    pdf["new_device"] = 0
    pdf["transactions_last_hour"] = 0

    # ======================================
    # RANDOM FOREST PREDICTION
    # ======================================

    print("Running ML risk prediction...")

    probabilities = model.predict_proba(
        pdf[FEATURE_COLUMNS]
    )[:, 1]

    pdf["fraud_probability"] = (
        probabilities.round(4)
    )

    pdf["risk_score"] = (
        probabilities * 100
    ).round().astype(int)

    pdf["risk_level"] = (
        pdf["risk_score"].apply(
            classify_risk
        )
    )

    # ======================================
    # ADWIN DRIFT DETECTION
    # ======================================

    print("Checking for data drift...")

    drift_events = []

    # Process transactions chronologically
    pdf = pdf.sort_values(
        "transaction_time"
    )

    for _, transaction in pdf.iterrows():

        drift_event = (
            drift_detector.check_transaction(
                transaction
            )
        )

        if drift_event is not None:

            # Identify the transaction that
            # triggered the drift warning

            drift_event["transaction_ref"] = str(
                transaction["transaction_ref"]
            )

            drift_event["customer_ref"] = str(
                transaction["customer_ref"]
            )

            drift_event["transaction_amount"] = float(
                transaction["amount"]
            )

            drift_event["transaction_time"] = str(
                transaction["transaction_time"]
            )

            drift_event["risk_score"] = int(
                transaction["risk_score"]
            )

            drift_event["risk_level"] = str(
                transaction["risk_level"]
            )

            drift_event["source"] = "spark_streaming"

            drift_events.append(drift_event)

            print("\n================================")
            print("WARNING: DATA DRIFT DETECTED!")
            print("================================")

            print(
                "Detector:",
                drift_event["detector_name"]
            )

            print(
                "Transaction Ref:",
                drift_event["transaction_ref"]
            )

            print(
                "Customer Ref:",
                drift_event["customer_ref"]
            )

            print(
                "Transaction Amount:",
                drift_event["transaction_amount"]
            )

            print(
                "Transaction Time:",
                drift_event["transaction_time"]
            )

            print(
                "Risk Score:",
                drift_event["risk_score"]
            )

            print(
                "Risk Level:",
                drift_event["risk_level"]
            )

            print(
                "Severity:",
                drift_event["severity"]
            )

            print(
                "Transactions Processed:",
                drift_event["transaction_count"]
            )

            print("================================\n")

    # ======================================
    # DISPLAY RISK PREDICTIONS
    # ======================================

    output_columns = [
        "transaction_ref",
        "customer_ref",
        "amount",
        "location",
        "risk_score",
        "risk_level",
        "fraud_probability",
    ]

    print(
        f"\n========== RISK BATCH {batch_id} =========="
    )

    print(
        pdf[output_columns].to_string(
            index=False
        )
    )

    # ======================================
    # BATCH SUMMARY
    # ======================================

    print("\n========== BATCH SUMMARY ==========")

    print(
        "Total Transactions:",
        len(pdf)
    )

    print(
        "LOW Risk:",
        int((pdf["risk_level"] == "LOW").sum())
    )

    print(
        "MEDIUM Risk:",
        int((pdf["risk_level"] == "MEDIUM").sum())
    )

    print(
        "HIGH Risk:",
        int((pdf["risk_level"] == "HIGH").sum())
    )

    print(
        "Drift Events in Batch:",
        len(drift_events)
    )

    print(
        "Total Drift Events:",
        drift_detector.total_drift_events
    )

    print("===================================\n")

    # ======================================
    # SAVE RESULTS INTO MYSQL
    # ======================================

    print("\nSaving Spark batch into MySQL...")

    try:

        save_risk_batch(
            pdf,
            drift_events=drift_events
        )

        print(
            f"Batch {batch_id} "
            "successfully saved into MySQL!"
        )

    except Exception as error:

        print(
            f"MySQL storage failed for "
            f"batch {batch_id}: {error}"
        )

        raise


# ==========================================
# 8. START SPARK STREAMING
# ==========================================

def main():

    print("\nStarting RiskGuard Streaming System...")

    spark = (
        SparkSession.builder
        .appName(
            "RiskGuardRealTimeRiskScoring"
        )
        .master("local[*]")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel(
        "ERROR"
    )

    print("Connecting to Kafka...")

    kafka_stream = (
        spark.readStream
        .format("kafka")
        .option(
            "kafka.bootstrap.servers",
            KAFKA_SERVER
        )
        .option(
            "subscribe",
            KAFKA_TOPIC
        )
        .option(
            "startingOffsets",
            "latest"
        )
        .load()
    )

    print("Kafka stream configured successfully!")

    transactions = (
        kafka_stream
        .select(
            from_json(
                col("value").cast("string"),
                transaction_schema
            ).alias("transaction")
        )
        .select("transaction.*")
    )

    query = (
        transactions.writeStream
        .foreachBatch(score_batch)
        .option(
            "checkpointLocation",
            str(CHECKPOINT_PATH)
        )
        .start()
    )

    print("\n===================================")
    print("RISKGUARD SYSTEM STARTED")
    print("===================================")

    print("Kafka Topic:", KAFKA_TOPIC)
    print("ML Model: Random Forest")
    print("Drift Detection: ADWIN")
    print("Database: MySQL (riskguard_db)")
    print("Streaming Status: ACTIVE")

    print("Waiting for banking transactions...")
    print("Press Ctrl+C to stop.\n")

    try:
        query.awaitTermination()

    except KeyboardInterrupt:
        print("\nStopping RiskGuard streaming...")

    finally:

        if query.isActive:
            query.stop()

        spark.stop()

        print("RiskGuard streaming stopped.")


if __name__ == "__main__":
    main()
