from ledger_engine.core.ledger import Ledger
from ledger_engine.models.transaction import Transaction
from ledger_engine.storage.snapshot_store import SnapshotStore


class ReplayEngine:

    def __init__(self, ledger: Ledger, snapshot_store: SnapshotStore):
        self.ledger = ledger
        self.snapshot_store = snapshot_store

    def restore_from_snapshot(self) -> int:
        snapshot = self.snapshot_store.load_latest_snapshot()

        if not snapshot:
            return 0

        # restore ledger state

        self.ledger.balances = snapshot["balances"]
        self.ledger.nonces = snapshot["nonces"]
        self.ledger.processed_ids = set(snapshot["processed_ids"])
        self.ledger.future_transactions = {
            sender: {
                int(nonce): Transaction(**tx_data) for nonce, tx_data in txs.items()
            }
            for sender, txs in snapshot.get("future_transactions", {}).items()
        }

        return snapshot["tx_index"]
