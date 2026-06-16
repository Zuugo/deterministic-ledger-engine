import hashlib
import json
from os import fsync
from pathlib import Path

from ledger_engine.models.transaction import Transaction


class TransactionJournal:

    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self.last_hash = "GENESIS"

    def append(self, tx: Transaction):

        record = {
            "tx_id": tx.tx_id,
            "sender": tx.sender,
            "receiver": tx.receiver,
            "amount": tx.amount,
            "nonce": tx.nonce,
            "timestamp": tx.timestamp.isoformat(),
        }

        record["previous_hash"] = self.last_hash

        current_hash = hashlib.sha256(
            json.dumps(record, sort_keys=True).encode()
        ).hexdigest()

        record["hash"] = current_hash

        self.last_hash = current_hash

        checksum = hashlib.sha256(
            json.dumps(record, sort_keys=True).encode()
        ).hexdigest()

        record["checksum"] = checksum

        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
            f.flush()
            fsync(f.fileno())

    def load_from(self, start_index: int):
        if not self.path.exists():
            return []

        transactions = []
        expected_previous_hash = "GENESIS"

        with open(self.path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i < start_index:
                    continue

                data = json.loads(line.strip())

                stored_checksum = data.pop("checksum")

                calculated_checksum = hashlib.sha256(
                    json.dumps(data, sort_keys=True).encode()
                ).hexdigest()

                if stored_checksum != calculated_checksum:
                    raise Exception(
                        f"Journal corruption detected at transaction {data['tx_id']}"
                    )

                if data["previous_hash"] != expected_previous_hash:
                    raise Exception(f"Broken hash chain at transaction {data['tx_id']}")

                stored_hash = data["hash"]

                record_for_hash = {
                    "tx_id": data["tx_id"],
                    "sender": data["sender"],
                    "receiver": data["receiver"],
                    "amount": data["amount"],
                    "nonce": data["nonce"],
                    "timestamp": data["timestamp"],
                    "previous_hash": data["previous_hash"],
                }

                calculated_hash = hashlib.sha256(
                    json.dumps(record_for_hash, sort_keys=True).encode()
                ).hexdigest()

                if stored_hash != calculated_hash:
                    raise Exception(f"Hash mismatch at transaction {data['tx_id']}")

                expected_previous_hash = stored_hash

                data.pop("previous_hash")
                data.pop("hash")

                transactions.append(Transaction(**data))

        return transactions
