import threading
import time

from django.utils.timezone import now

from ledger_engine.core.ledger import Ledger
from ledger_engine.exceptions.exceptions import (
    DuplicateTransactionError,
    FutureNonceError,
    InsufficientBalanceError,
    InvalidNonceError,
    LedgerError,
)
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
        snapshot_interval: int = 5,
    ):
        self.ledger = ledger
        self.journal = journal
        self.snapshot_store = snapshot_store
        self.replay_engine = replay_engine
        self.validate = validate
        self.snapshot_interval = snapshot_interval

        self.lock = threading.Lock()
        self.tx_count = 0
        self.tx_since_snapshot = 0

    def start(self):

        # restore ledger state on startup

        snapshot_index = self.replay_engine.restore_from_snapshot()
        transactions = self.journal.load_from(snapshot_index)

        print(f"[REPLAY] snapshot_index={snapshot_index}")
        print(f"[REPLAY] replay_count={len(transactions)}")

        for tx in transactions:
            print(f"[REPLAY TX] {tx.tx_id}")
            if not self.ledger.apply_transaction(tx):
                raise RuntimeError("Ledger replay failed - journal corrupted")

        print(f"[REPLAY STATE]")
        print(self.ledger.balances)
        print(self.ledger.nonces)
        print(self.ledger.processed_ids)

        self.replay_engine.reconcile_transaction_statuses()

    def process(self, tx: Transaction):
        if tx.tx_id == "TEST_RECOVERY2":
            print(f"[TEST] Simulating crash")
            time.sleep(15)

        if not self.validate.validate(tx):
            return False, "Invalid Transaction", False

        # process a new transaction

        with self.lock:
            try:
                self.ledger.apply_transaction(tx)

            except FutureNonceError:
                return False, "Buffered future transaction", False

            except DuplicateTransactionError:
                return False, "Duplicate transaction", False

            except InvalidNonceError:
                return False, "Invalid nonce", False

            except InsufficientBalanceError:
                return False, "Insufficient balance", False

            except Exception as e:
                return False, f"System error: {str(e)}", True

            self.journal.append(tx)
            self.tx_count += 1
            self.tx_since_snapshot += 1

            if self.tx_since_snapshot >= self.snapshot_interval:
                self.snapshot_store.save_snapshot(self.ledger, self.tx_count)
                self.tx_since_snapshot = 0

            promoted = self.ledger.get_processable_buffered(tx.sender)

            if promoted:
                print(f"[PROMOTE BUFFER] {promoted.tx_id}")

                from ledger.models import TransactionQueue, TransactionStatus

                TransactionQueue.objects.filter(
                    tx_id=promoted.tx_id,
                ).update(
                    status="PENDING",
                    next_attempt=now(),
                )

                TransactionStatus.objects.update_or_create(
                    tx_id=promoted.tx_id,
                    defaults={
                        "status": "PENDING",
                        "reason": None,
                    },
                )

            return True, None, False
