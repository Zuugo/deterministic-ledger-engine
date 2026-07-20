import threading
import time

from django.utils.timezone import now

from ledger_engine.core.ledger import Ledger
from ledger_engine.exceptions.exceptions import (
    DuplicateTransactionError,
    FutureNonceError,
    InsufficientBalanceError,
    InvalidNonceError,
)
from ledger_engine.models.process_result import ProcessResult
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

    def process(self, tx: Transaction) -> ProcessResult:

        if not self.validate.validate(tx):
            return ProcessResult(success=False, reason="Invalid Transaction")

        # process a new transaction

        with self.lock:

            result = self._apply_transaction(tx)

            if result is not None:
                return result

            self.journal.append(tx)

            journal_position = self.journal.get_position()

            result = ProcessResult(success=True, journal_position=journal_position)

            if journal_position % self.snapshot_interval == 0:

                snapshot_id = int(time.time_ns())

                self.snapshot_store.save_snapshot(
                    self.ledger, snapshot_id, self.journal.last_hash, journal_position
                )
                self.tx_since_snapshot = 0

                result.snapshot_created = True
                result.snapshot_id = snapshot_id

            promoted = self.ledger.pop_processable_buffered(tx.sender)

            while promoted:

                result.promoted_transactions.append(promoted)
                promoted = self.ledger.pop_processable_buffered(tx.sender)

            return result

    def _apply_transaction(self, tx: Transaction) -> ProcessResult | None:

        try:
            self.ledger.apply_transaction(tx)

            return None

        except FutureNonceError:

            return ProcessResult(
                success=False,
                reason="Buffered future transaction",
            )

        except DuplicateTransactionError:

            return ProcessResult(
                success=False,
                reason="Duplicate transaction",
            )

        except InvalidNonceError:

            return ProcessResult(
                success=False,
                reason="Invalid nonce",
            )

        except InsufficientBalanceError:

            return ProcessResult(
                success=False,
                reason="Insufficient balance",
            )

        except Exception as e:

            return ProcessResult(
                success=False,
                reason=f"System error: {e}",
                retryable=True,
            )
