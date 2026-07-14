from ledger_engine.core.ledger import Ledger
from ledger_engine.models.snapshot import Snapshot
from ledger_engine.storage.snapshot_store import SnapshotStore


class ReplayEngine:

    def __init__(
        self,
        ledger: Ledger,
        snapshot_store: SnapshotStore,
    ):
        self.ledger = ledger
        self.snapshot_store = snapshot_store

    def restore_from_snapshot(self) -> Snapshot | None:

        snapshot = self.snapshot_store.load_latest_snapshot()

        if snapshot is None:
            return None

        snapshot.restore(self.ledger)

        return snapshot
