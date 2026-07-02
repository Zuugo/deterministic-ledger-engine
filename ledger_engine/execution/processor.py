import os
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

        from ledger.services.startup_service import StartupService

        StartupService(self).start()

    def process(self, tx: Transaction):
        from ledger.models import LedgerEvent
        from ledger.services.event_service import EventService

        """
        if tx.tx_id == "TEST_RECOVERY2":
            print(f"[TEST] Simulating recovery")
            time.sleep(15)

        if tx.tx_id == "TEST_CRASH":
            print(f"[TEST] Simulating crash")
            os._exit(1)

        
        if tx.tx_id == "TEST_DLQ3":
            print(f"[TEST] Simulating permanent failure")
            return False, "Permanent failure for DLQ testing", False
        """
        if not self.validate.validate(tx):
            return False, "Invalid Transaction", False

        # process a new transaction

        with self.lock:
            try:
                self.ledger.apply_transaction(tx)

            except FutureNonceError:
                EventService.emit(
                    tx.tx_id,
                    "TX_BUFFERED",
                    {
                        "sender": tx.sender,
                        "nonces": tx.nonce,
                    },
                )
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

            journal_position = self.journal.get_position()
            snapshot_id = int(time.time_ns())

            if journal_position % self.snapshot_interval == 0:

                self.snapshot_store.save_snapshot(
                    self.ledger, snapshot_id, self.journal.last_hash, journal_position
                )
                self.tx_since_snapshot = 0

            promoted = self.ledger.get_processable_buffered(tx.sender)

            if promoted:

                from ledger.models import TransactionQueue, TransactionStatus
                from ledger.services.lifecycle_service import (
                    TransactionLifecycleService,
                )

                print(f"[PROMOTE BUFFER] {promoted.tx_id}")

                EventService.emit(
                    promoted.tx_id,
                    "BUFFER_PROMOTED",
                    {
                        "sender": promoted.sender,
                        "nonces": promoted.nonce,
                    },
                )

                TransactionQueue.objects.filter(
                    tx_id=promoted.tx_id,
                ).update(
                    status="PENDING",
                    next_attempt=now(),
                )

                TransactionLifecycleService.transition(
                    tx_id=promoted.tx_id,
                    status="PENDING",
                )

            return True, None, False
