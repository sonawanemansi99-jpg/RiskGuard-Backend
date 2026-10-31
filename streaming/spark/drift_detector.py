
import math
from river import drift


class RiskGuardDriftDetector:

    def __init__(self):
        # ADWIN monitors changes in transaction amounts.
        self.amount_detector = drift.ADWIN(delta=0.002)

        self.total_transactions = 0
        self.total_drift_events = 0

    def check_transaction(self, transaction):
        amount = float(transaction["amount"])

        # Log transformation reduces the effect
        # of extremely large transaction amounts.
        normalized_amount = math.log1p(max(amount, 0))

        self.amount_detector.update(normalized_amount)

        self.total_transactions += 1

        if self.amount_detector.drift_detected:
            self.total_drift_events += 1

            event = {
                "detector_name": "ADWIN_AMOUNT",
                "drift_detected": True,
                "severity": "MEDIUM",
                "details": (
                    "Change detected in the distribution "
                    "of transaction amounts."
                ),
                "transaction_count": self.total_transactions,
            }

            print("\n================================")
            print("WARNING: DATA DRIFT DETECTED!")
            print("Detector: ADWIN_AMOUNT")
            print(
                "Transactions processed:",
                self.total_transactions
            )
            print("================================\n")

            return event

        return None
