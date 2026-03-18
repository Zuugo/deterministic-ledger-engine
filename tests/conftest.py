import os
import shutil
import time

import pytest

from ledger_engine.core.ledger import Ledger
from ledger_engine.execution.processor import TransactionProcessor
from ledger_engine.models.transaction import Transaction
from ledger_engine.replay.replay_engine import ReplayEngine
from ledger_engine.storage.snapshot_store import SnapshotStore
from ledger_engine.storage.transaction_journal import TransactionJournal
from ledger_engine.validation.validator import TransactionValidator


@pytest.fixture
def clean_data():
    if os.path.exists("data"):
        shutil.rmtree("data")
    os.mkdir("data")


@pytest.fixture
def system(clean_data):
    ledger = Ledger()
    journal = TransactionJournal("data/journal.log")
    snapshot_store = SnapshotStore("data")
    replay = ReplayEngine(ledger, snapshot_store)
    validator = TransactionValidator()

    processor = TransactionProcessor(
        ledger, journal, snapshot_store, replay, validator, snapshot_interval=2
    )

    processor.start()

    return processor, ledger


@pytest.fixture
def tx_factory():
    def _tx(i, sender, receiver, amount, nonce):
        return Transaction(
            tx_id=str(i),
            sender=sender,
            receiver=receiver,
            amount=amount,
            nonce=nonce,
            timestamp=time.time(),
        )

    return _tx
