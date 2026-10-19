
import json
import random
import time
import uuid
from datetime import datetime, timezone

from kafka import KafkaProducer
from kafka.errors import KafkaError

BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "bank_transactions"

LOCATIONS = ["Pune", "Mumbai", "Nashik", "Delhi", "Bengaluru"]
MERCHANT_CATEGORIES = [
    "Retail",
    "Grocery",
    "Travel",
    "Electronics",
    "Restaurant",
    "Online"
]


def generate_transaction():
    """Generate one sample banking transaction."""

    transaction = {
        "transaction_ref": f"TXN_{uuid.uuid4().hex[:12].upper()}",
        "customer_ref": f"CUST_{random.randint(1001, 1100)}",
        "amount": round(random.uniform(100, 100000), 2),
        "currency": "INR",
        "location": random.choice(LOCATIONS),
        "device_id": f"DEV_{random.randint(100, 130)}",
        "merchant_category": random.choice(MERCHANT_CATEGORIES),
        "transaction_time": datetime.now(timezone.utc).isoformat()
    }

    return transaction


def main():
    producer = None

    try:
        producer = KafkaProducer(
            bootstrap_servers=BOOTSTRAP_SERVERS,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
            key_serializer=lambda key: key.encode("utf-8"),
            acks="all",
            retries=5
        )

        print(f"Connected to Kafka at {BOOTSTRAP_SERVERS}")
        print(f"Publishing transactions to topic: {TOPIC}")
        print("Press Ctrl+C to stop.\n")

        while True:
            transaction = generate_transaction()

            future = producer.send(
                TOPIC,
                key=transaction["transaction_ref"],
                value=transaction
            )

            # Wait for Kafka to acknowledge this message.
            metadata = future.get(timeout=10)

            print(
                f"Published | topic={metadata.topic} "
                f"partition={metadata.partition} "
                f"offset={metadata.offset} | "
                f"transaction={json.dumps(transaction)}"
            )

            time.sleep(2)

    except KeyboardInterrupt:
        print("\nStopping transaction producer...")

    except KafkaError as error:
        print(f"Kafka error: {error}")

    finally:
        if producer is not None:
            producer.flush()
            producer.close()

        print("Producer stopped.")


if __name__ == "__main__":
    main()
