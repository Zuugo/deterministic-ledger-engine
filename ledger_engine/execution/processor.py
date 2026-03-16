import threading

from ledger_engine.core.ledger import Ledger
from ledger_engine.models.transaction import Transaction
from ledger_engine.replay.replay_engine import ReplayEngine
from ledger_engine.storage.snapshot_store import SnapshotStore
from ledger_engine.storage.transaction_journal import TransactionJournal
from ledger_engine.validation.validator import TransactionValidator


class TransactionProcessor:

    def __init__(
        self,
        ledger: Ledger,
        journal: TransactionJournal,
        snapshot_store: SnapshotStore,
        replay_engine: ReplayEngine,
        validate: TransactionValidator,
        snapshot_interval: int = 1000,
    ):
        self.ledger = ledger
        self.journal = journal
        self.snapshot_store = snapshot_store
        self.replay_engine = replay_engine
        self.validate = validate
        self.snapshot_interval = snapshot_interval

        self.lock = threading.Lock()
        self.tx_since_snapshot = 0

    def start(self):

        # restore ledger state on startup

        snapshot_index = self.replay_engine.restore_from_snapshot(self.ledger)
        transactions = self.journal.load_from(snapshot_index)

        for tx in transactions:
            if not self.ledger.apply_transaction(tx):
                raise RuntimeError("Ledger replay failed - journal corrupted")

    def process(self, tx: Transaction) -> bool:
        if not self.validate.validate(tx):
            return False

        # process a new transaction

        with self.lock:

            success = self.ledger.apply_transaction(tx)

            if not success:
                return False

            self.journal.append(tx)
            self.tx_since_snapshot += 1

            if self.tx_since_snapshot >= self.snapshot_interval:
                self.snapshot_store.save_snapshot(self.ledger)
                self.tx_since_snapshot = 0

            return True
