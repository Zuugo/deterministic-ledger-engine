import json
from os import fsync
from pathlib import Path

from ledger_engine.models.journal_record import JournalRecord
from ledger_engine.models.transaction import Transaction


class TransactionJournal:

    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self.last_hash = self._load_last_hash()

    def append(self, tx: Transaction) -> None:
        record = JournalRecord.from_transaction(
            tx=tx,
            previous_hash=self.last_hash,
        )

        record.compute_hash()
        record.compute_checksum()

        self.last_hash = record.hash

        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict()) + "\n")
            f.flush()
            fsync(f.fileno())

    def load_from(self, start_index: int) -> list[Transaction]:

        transactions = []

        for index, record in enumerate(self._iterate_records()):

            if index < start_index:
                continue

            transactions.append(record.to_transaction())

        return transactions

    def load_after_hash(self, target_hash: str) -> list[Transaction]:

        transactions = []
        found = False

        for record in self._iterate_records():

            if found:
                transactions.append(record.to_transaction())

            if record.hash == target_hash:
                found = True

        return transactions

    @property
    def entry_count(self) -> int:

        if not self.path.exists():
            return 0

        with open(self.path, "r", encoding="utf-8") as f:
            return sum(1 for _ in f)

    def _iterate_records(self):

        if not self.path.exists():
            return

        with open(self.path, "r", encoding="utf-8") as f:

            for line in f:

                if not line.strip():
                    continue

                record = JournalRecord.from_dict(json.loads(line))

                record.verify()

                yield record

    def _load_last_hash(self) -> str:

        if not self.path.exists():
            return "GENESIS"

        last_record = None

        with open(self.path, "r", encoding="utf-8") as f:

            for line in f:

                if line.strip():
                    last_record = JournalRecord.from_dict(json.loads(line))

        if last_record is None:
            return "GENESIS"

        return last_record.hash
