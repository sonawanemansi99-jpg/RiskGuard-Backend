
import json

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    DoubleType,
)


KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
KAFKA_TOPIC = "bank_transactions"


def main():
    spark = (
        SparkSession.builder
        .appName("RiskGuardTransactionStreaming")
        .master("local[*]")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    # Schema of the JSON messages produced by producer.py
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

    print("Connecting Spark Structured Streaming to Kafka...")
    print(f"Kafka topic: {KAFKA_TOPIC}")

    # Read messages continuously from Kafka.
    kafka_stream = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribe", KAFKA_TOPIC)
        .option("startingOffsets", "latest")
        .load()
    )

    # Convert Kafka's binary message value to a JSON string.
    json_stream = kafka_stream.select(
        col("value").cast("string").alias("json")
    )

    # Parse each JSON message into structured transaction columns.
    transactions = (
        json_stream
        .select(
            from_json(col("json"), transaction_schema).alias("transaction")
        )
        .select("transaction.*")
    )

    # Display each arriving batch in the terminal.
    query = (
        transactions.writeStream
        .format("console")
        .outputMode("append")
        .option("truncate", "false")
        .option("checkpointLocation", "./checkpoints/transactions")
        .start()
    )

    print("Spark streaming is running. Press Ctrl+C to stop.")

    try:
        query.awaitTermination()
    except KeyboardInterrupt:
        print("Stopping Spark streaming...")
    finally:
        query.stop()
        spark.stop()


if __name__ == "__main__":
    main()
