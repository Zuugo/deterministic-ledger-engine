from datetime import UTC, datetime

from ledger_engine.core.ledger import Ledger
from ledger_engine.execution.processor import TransactionProcessor
from ledger_engine.models.transaction import Transaction
from ledger_engine.replay.replay_engine import ReplayEngine
from ledger_engine.storage.snapshot_store import SnapshotStore
from ledger_engine.storage.transaction_journal import TransactionJournal
from ledger_engine.validation.validator import TransactionValidator


def create_processor(tmp_path):
    ledger = Ledger()

    journal = TransactionJournal(tmp_path / "journal.log")

    snapshot_store = SnapshotStore(tmp_path)

    replay_engine = ReplayEngine(
        ledger=ledger,
        snapshot_store=snapshot_store,
    )

    validator = TransactionValidator()

    return TransactionProcessor(
        ledger=ledger,
        journal=journal,
        snapshot_store=snapshot_store,
        replay_engine=replay_engine,
        validate=validator,
        snapshot_interval=5,
    )


def tx(tx_id, sender, receiver, amount, nonce):
    return Transaction(
        tx_id=tx_id,
        sender=sender,
        receiver=receiver,
        amount=amount,
        nonce=nonce,
        timestamp=datetime.now(UTC),
    )


def test_process_system_transaction(tmp_path):
    processor = create_processor(tmp_path)

    result = processor.process(tx("1", "SYSTEM", "Alice", 100, 1))

    assert result.success
    assert processor.ledger.balances["Alice"] == 100
    assert processor.journal.entry_count == 1


def test_invalid_transaction_rejected(tmp_path):
    processor = create_processor(tmp_path)

    result = processor.process(tx("1", "", "", -10, 1))

    assert not result.success
    assert result.reason == "Invalid Transaction"
    assert processor.journal.entry_count == 0


def test_duplicate_transaction(tmp_path):
    processor = create_processor(tmp_path)

    processor.process(tx("1", "SYSTEM", "Alice", 100, 1))

    result = processor.process(tx("1", "SYSTEM", "Alice", 100, 1))

    assert not result.success
    assert result.reason == "Duplicate transaction"


def test_successful_transaction_written_to_journal(tmp_path):
    processor = create_processor(tmp_path)

    processor.process(tx("1", "SYSTEM", "Alice", 50, 1))

    assert processor.journal.entry_count == 1


def test_process_result_contains_journal_position(tmp_path):
    processor = create_processor(tmp_path)

    result = processor.process(tx("1", "SYSTEM", "Alice", 100, 1))

    assert result.success
    assert result.journal_position == 1


def test_snapshot_created(tmp_path):
    processor = create_processor(tmp_path)

    for i in range(5):
        result = processor.process(
            tx(
                str(i),
                "SYSTEM",
                "Alice",
                10,
                i + 1,
            )
        )

    assert result.snapshot_created


def test_future_nonce_buffered(tmp_path):
    processor = create_processor(tmp_path)

    processor.process(tx("1", "SYSTEM", "Alice", 100, 1))

    result = processor.process(tx("2", "Alice", "Bob", 20, 2))

    assert not result.success
    assert result.reason == "Buffered future transaction"


def test_buffered_transaction_promoted(tmp_path):
    processor = create_processor(tmp_path)

    processor.process(tx("1", "SYSTEM", "Alice", 100, 1))

    processor.process(tx("2", "Alice", "Bob", 20, 2))

    result = processor.process(tx("3", "Alice", "Bob", 20, 1))

    assert result.success
    assert len(result.promoted_transactions) == 1
    assert result.promoted_transactions[0].tx_id == "2"


def test_nonce_updated(tmp_path):
    processor = create_processor(tmp_path)

    processor.process(tx("1", "SYSTEM", "Alice", 100, 1))

    processor.process(tx("2", "Alice", "Bob", 10, 1))

    assert processor.ledger.nonces["Alice"] == 1


def test_balance_updated(tmp_path):
    processor = create_processor(tmp_path)

    processor.process(tx("1", "SYSTEM", "Alice", 100, 1))

    processor.process(tx("2", "Alice", "Bob", 40, 1))

    assert processor.ledger.balances["Alice"] == 60
    assert processor.ledger.balances["Bob"] == 40
