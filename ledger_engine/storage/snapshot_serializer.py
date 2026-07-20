import copy
from datetime import datetime

from ledger_engine.core.ledger import Ledger
from ledger_engine.models.snapshot import Snapshot
from ledger_engine.models.transaction import Transaction


class SnapshotSerializer:

    @staticmethod
    def serialize(
        ledger: Ledger,
        snapshot_id: int,
        last_hash: str,
        journal_position: int,
    ) -> dict:

        return {
            "snapshot_id": snapshot_id,
            "journal_position": journal_position,
            "last_hash": last_hash,
            "balances": copy.deepcopy(ledger.balances),
            "nonces": copy.deepcopy(ledger.nonces),
            "processed_ids": list(ledger.processed_ids),
            "future_transactions": {
                sender: {
                    nonce: {
                        "tx_id": tx.tx_id,
                        "sender": tx.sender,
                        "receiver": tx.receiver,
                        "amount": tx.amount,
                        "nonce": tx.nonce,
                        "timestamp": tx.timestamp.isoformat(),
                    }
                    for nonce, tx in txs.items()
                }
                for sender, txs in ledger.future_transactions.items()
            },
        }

    @staticmethod
    def deserialize(snapshot: dict) -> Snapshot:

        future_transactions = {
            sender: {
                int(nonce): Transaction(
                    tx_id=tx_data["tx_id"],
                    sender=tx_data["sender"],
                    receiver=tx_data["receiver"],
                    amount=tx_data["amount"],
                    nonce=tx_data["nonce"],
                    timestamp=datetime.fromisoformat(tx_data["timestamp"]),
                )
                for nonce, tx_data in txs.items()
            }
            for sender, txs in snapshot.get("future_transactions", {}).items()
        }

        return Snapshot(
            snapshot_id=snapshot["snapshot_id"],
            journal_position=snapshot["journal_position"],
            last_hash=snapshot["last_hash"],
            balances=snapshot.get("balances", {}),
            nonces=snapshot.get("nonces", {}),
            processed_ids=snapshot.get("processed_ids", []),
            future_transactions=future_transactions,
        )
