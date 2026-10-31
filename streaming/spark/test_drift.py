
import random
import json

from drift_detector import RiskGuardDriftDetector
from mysql_writer import get_connection


# ==========================================
# 1. INITIALIZE DRIFT DETECTOR
# ==========================================

random.seed(42)

detector = RiskGuardDriftDetector()

drift_events = []


# ==========================================
# 2. TEST NORMAL TRANSACTIONS
# ==========================================

print("Testing normal transaction pattern...")

for i in range(1000):

    amount = random.uniform(500, 3000)

    transaction_ref = f"TEST_NORMAL_{i + 1}"

    event = detector.check_transaction({
        "amount": amount
    })

    if event is not None:

        event["transaction_ref"] = transaction_ref
        event["transaction_amount"] = amount
        event["transaction_number"] = (
            detector.total_transactions
        )
        event["source"] = "test_drift.py"

        drift_events.append(event)

        print("\nDRIFT DETECTED!")
        print("Transaction:", transaction_ref)
        print("Amount:", round(amount, 2))


# ==========================================
# 3. TEST CHANGED TRANSACTIONS
# ==========================================

print("Testing changed transaction pattern...")

for i in range(1000):

    amount = random.uniform(50000, 100000)

    transaction_ref = f"TEST_DRIFT_{i + 1001}"

    event = detector.check_transaction({
        "amount": amount
    })

    if event is not None:

        event["transaction_ref"] = transaction_ref
        event["transaction_amount"] = amount
        event["transaction_number"] = (
            detector.total_transactions
        )
        event["source"] = "test_drift.py"

        drift_events.append(event)

        print("\n================================")
        print("WARNING: DATA DRIFT DETECTED!")
        print("================================")

        print("Transaction:", transaction_ref)
        print("Amount:", round(amount, 2))

        print(
            "Transaction Number:",
            detector.total_transactions
        )

        print("================================\n")


# ==========================================
# 4. DISPLAY TEST SUMMARY
# ==========================================

print("\n================================")
print("DRIFT TEST COMPLETED")
print("================================")

print(
    "Total Transactions:",
    detector.total_transactions
)

print(
    "Total Drift Events:",
    len(drift_events)
)


# ==========================================
# 5. SAVE DRIFT EVENTS TO MYSQL
# ==========================================

if drift_events:

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        print("\nConnected to MySQL database.")

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
                )
            )

        connection.commit()

        print(
            "Drift events saved to MySQL:",
            len(drift_events)
        )

    except Exception as error:

        if connection is not None:
            connection.rollback()

        print("MySQL storage error:", error)
        raise

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()

else:

    print("No drift events detected.")
    print("Nothing to save in MySQL.")
