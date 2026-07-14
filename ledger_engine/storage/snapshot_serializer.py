import copy

from ledger_engine.core.ledger import Ledger
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
                sender: {nonce: tx.__dict__ for nonce, tx in txs.items()}
                for sender, txs in ledger.future_transactions.items()
            },
        }

    @staticmethod
    def deserialize(snapshot: dict, ledger: Ledger) -> None:
        """
        Restores a Ledger instance from a persisted snapshot.
        """

        ledger.balances = snapshot.get("balances", {})

        ledger.nonces = snapshot.get("nonces", {})

        ledger.processed_ids = set(snapshot.get("processed_ids", []))

        ledger.future_transactions = {
            sender: {
                int(nonce): Transaction(**tx_data) for nonce, tx_data in txs.items()
            }
            for sender, txs in snapshot.get(
                "future_transactions",
                {},
            ).items()
        }
