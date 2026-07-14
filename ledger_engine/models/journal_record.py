import hashlib
import json
from dataclasses import dataclass

from ledger_engine.exceptions.exceptions import JournalCorruptionError
from ledger_engine.models.transaction import Transaction


@dataclass
class JournalRecord:
    tx_id: str
    sender: str
    receiver: str | None
    amount: int
    nonce: int
    timestamp: str
    previous_hash: str
    hash: str | None = None
    checksum: str | None = None

    @classmethod
    def from_transaction(
        cls,
        tx: Transaction,
        previous_hash: str,
    ) -> "JournalRecord":
        return cls(
            tx_id=tx.tx_id,
            sender=tx.sender,
            receiver=tx.receiver,
            amount=tx.amount,
            nonce=tx.nonce,
            timestamp=tx.timestamp.isoformat(),
            previous_hash=previous_hash,
        )

    @classmethod
    def from_dict(cls, data: dict) -> "JournalRecord":
        return cls(
            tx_id=data["tx_id"],
            sender=data["sender"],
            receiver=data["receiver"],
            amount=data["amount"],
            nonce=data["nonce"],
            timestamp=data["timestamp"],
            previous_hash=data["previous_hash"],
            hash=data.get("hash"),
            checksum=data.get("checksum"),
        )

    def to_dict(self) -> dict:
        return {
            "tx_id": self.tx_id,
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "nonce": self.nonce,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "hash": self.hash,
            "checksum": self.checksum,
        }

    def to_transaction(self) -> Transaction:
        return Transaction(
            tx_id=self.tx_id,
            sender=self.sender,
            receiver=self.receiver,
            amount=self.amount,
            nonce=self.nonce,
            timestamp=self.timestamp,
        )

    def compute_hash(self) -> str:
        record = {
            "tx_id": self.tx_id,
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "nonce": self.nonce,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
        }

        self.hash = hashlib.sha256(
            json.dumps(record, sort_keys=True).encode()
        ).hexdigest()

        return self.hash

    def compute_checksum(self) -> str:
        if self.hash is None:
            raise ValueError("Hash must be computed before checksum.")

        record = self.to_dict()
        record.pop("checksum")

        self.checksum = hashlib.sha256(
            json.dumps(record, sort_keys=True).encode()
        ).hexdigest()

        return self.checksum

    def verify(self) -> None:
        if self.hash is None:
            raise JournalCorruptionError("Missing journal hash.")

        if self.checksum is None:
            raise JournalCorruptionError("Missing journal checksum.")

        expected_hash = hashlib.sha256(
            json.dumps(
                {
                    "tx_id": self.tx_id,
                    "sender": self.sender,
                    "receiver": self.receiver,
                    "amount": self.amount,
                    "nonce": self.nonce,
                    "timestamp": self.timestamp,
                    "previous_hash": self.previous_hash,
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()

        if expected_hash != self.hash:
            raise JournalCorruptionError(f"Hash mismatch for transaction {self.tx_id}")

        expected_checksum = hashlib.sha256(
            json.dumps(
                {
                    "tx_id": self.tx_id,
                    "sender": self.sender,
                    "receiver": self.receiver,
                    "amount": self.amount,
                    "nonce": self.nonce,
                    "timestamp": self.timestamp,
                    "previous_hash": self.previous_hash,
                    "hash": self.hash,
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()

        if expected_checksum != self.checksum:
            raise JournalCorruptionError(
                f"Checksum mismatch for transaction {self.tx_id}"
            )
