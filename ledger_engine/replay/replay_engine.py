from ledger_engine.core.ledger import Ledger
from ledger_engine.storage.snapshot_store import SnapshotStore


class ReplayEngine:

    def __init__(self, ledger: Ledger, snapshot_store: SnapshotStore):
        self.ledger = ledger
        self.snapshot_store = snapshot_store

    def restore_from_snapshot(self):
        snapshot = self.snapshot_store.load_latest_snapshot()

        if not snapshot:
            return 0

        # restore ledger state

        self.ledger.balances = snapshot["balances"]
        self.ledger.nonces = snapshot["nonces"]
        self.ledger.processed_ids = set(snapshot["processed_ids"])

        return snapshot["tx_index"]
