
import json
import os

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv


# ==========================================
# 1. LOAD EXISTING BACKEND .ENV FILE
# ==========================================

# Current file:
# banking-risk-system/streaming/spark/mysql_writer.py
#
# Existing environment file:
# banking-risk-system/backend/.env

BASE_DIR = Path(__file__).resolve().parents[2]

BACKEND_ENV = BASE_DIR / "backend" / ".env"

if not BACKEND_ENV.exists():
    raise FileNotFoundError(
        f"Backend .env file not found: {BACKEND_ENV}"
    )

load_dotenv(BACKEND_ENV)

print("Backend environment configuration loaded.")


# ==========================================
# 2. MYSQL DATABASE CONNECTION
# ==========================================

def get_connection():

    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")

    # Supports DB_NAME or DB_DATABASE
    db_name = (
        os.getenv("DB_NAME")
        or os.getenv("DB_DATABASE")
        or "riskguard_db"
    )

    if not db_user:
        raise ValueError(
            "DB_USER is missing from backend/.env"
        )

    if db_password is None:
        raise ValueError(
            "DB_PASSWORD is missing from backend/.env"
        )

    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=db_user,
        password=db_password,
        database=db_name,
        connection_timeout=10,
    )

    return connection


# ==========================================
# 3. CONVERT TIMESTAMP TO MYSQL DATETIME
# ==========================================

def to_mysql_datetime(value):

    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

    if dt.tzinfo is None:
        raise ValueError(
            "Transaction timestamp must include timezone"
        )

    return (
        dt.astimezone(timezone.utc)
        .replace(tzinfo=None)
    )


# ==========================================
# 4. SAVE SPARK BATCH INTO MYSQL
# ==========================================

def save_risk_batch(pdf, drift_events=None):

    """
    Save Spark transaction results into MySQL.

    Tables:
        transactions
        risk_assessments
        drift_events

    Uses a database transaction and unique constraints
    to avoid duplicate transaction records.
    """

    drift_events = drift_events or []

    connection = None
    cursor = None

    saved = 0

    try:

        # ----------------------------------
        # Establish database connection
        # ----------------------------------

        connection = get_connection()
        cursor = connection.cursor()

        connection.start_transaction()

        print("\nConnected to RiskGuard MySQL database.")

        # ----------------------------------
        # Save transactions and assessments
        # ----------------------------------

        for row in pdf.to_dict(orient="records"):

            transaction_ref = str(
                row["transaction_ref"]
            )

            customer_ref = str(
                row["customer_ref"]
            )

            amount = Decimal(
                str(row["amount"])
            )

            transaction_time = to_mysql_datetime(
                row["transaction_time"]
            )

            # Insert transaction if not already present.
            # LAST_INSERT_ID returns the existing ID
            # when the transaction reference is duplicated.

            cursor.execute(
                """
                INSERT INTO transactions (
                    transaction_ref,
                    customer_ref,
                    amount,
                    currency,
                    location,
                    device_id,
                    merchant_category,
                    transaction_time
                )
                VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
                ON DUPLICATE KEY UPDATE
                    id = LAST_INSERT_ID(id)
                """,
                (
                    transaction_ref,
                    customer_ref,
                    amount,
                    str(row.get("currency") or "INR"),
                    row.get("location"),
                    row.get("device_id"),
                    row.get("merchant_category"),
                    transaction_time,
                ),
            )

            transaction_id = cursor.lastrowid

            if not transaction_id:
                raise RuntimeError(
                    f"Could not resolve ID for {transaction_ref}"
                )

            # ----------------------------------
            # Save ML risk assessment
            # ----------------------------------

            risk_score = int(
                row["risk_score"]
            )

            risk_level = str(
                row["risk_level"]
            )

            fraud_probability = Decimal(
                str(row["fraud_probability"])
            )

            reasons = json.dumps({
                "method": "Random Forest",
                "description": (
                    "ML-based transaction risk prediction"
                ),
                "note": (
                    "Prototype scoring uses temporary "
                    "customer-history feature defaults"
                ),
            })

            cursor.execute(
                """
                INSERT INTO risk_assessments (
                    transaction_id,
                    risk_score,
                    risk_level,
                    fraud_probability,
                    reasons,
                    model_version
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s
                )
                ON DUPLICATE KEY UPDATE
                    risk_score = VALUES(risk_score),
                    risk_level = VALUES(risk_level),
                    fraud_probability = VALUES(fraud_probability),
                    reasons = VALUES(reasons),
                    model_version = VALUES(model_version)
                """,
                (
                    transaction_id,
                    risk_score,
                    risk_level,
                    fraud_probability,
                    reasons,
                    "v1",
                ),
            )

            saved += 1

        # ----------------------------------
        # Save ADWIN drift events
        # ----------------------------------

        for event in drift_events:

            cursor.execute(
                """
                INSERT INTO drift_events (
                    detector_name,
                    drift_detected,
                    severity,
                    details
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    event["detector_name"],
                    1 if event.get(
                        "drift_detected", True
                    ) else 0,
                    event.get("severity", "MEDIUM"),
                    json.dumps(event),
                ),
            )

        # ----------------------------------
        # Commit database changes
        # ----------------------------------

        connection.commit()

        print("\n===================================")
        print("RISKGUARD MYSQL STORAGE SUCCESSFUL")
        print("===================================")

        print("Transactions processed:", saved)

        print("Risk assessments saved:", saved)

        print(
            "Drift events saved:",
            len(drift_events)
        )

        print("Database:", connection.database)

        print("===================================\n")

    except Exception as error:

        if connection is not None:
            connection.rollback()

        print("\nMySQL storage error:", error)

        raise

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()
