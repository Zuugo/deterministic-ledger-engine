import json
from os import fsync
from pathlib import Path

from ledger_engine.models.transaction import Transaction


class TransactionJournal:

    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, tx: Transaction):
        record = {
            "tx_id": tx.tx_id,
            "sender": tx.sender,
            "receiver": tx.receiver,
            "amount": tx.amount,
            "nonce": tx.nonce,
            "timestamp": tx.timestamp.isoformat(),
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
            f.flush()
            fsync(f.fileno())

    def load_from(self, start_index: int):
        if not self.path.exists():
            return []

        transactions = []

        with open(self.path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i < start_index:
                    continue

                data = json.loads(line.strip())
                transactions.append(Transaction(**data))

        return transactions
