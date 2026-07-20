from datetime import UTC, datetime

from ledger_engine.core.ledger import Ledger
from ledger_engine.models.transaction import Transaction
from ledger_engine.replay.replay_engine import ReplayEngine
from ledger_engine.storage.snapshot_store import SnapshotStore


def tx(tx_id, sender, receiver, amount, nonce):
    return Transaction(
        tx_id=tx_id,
        sender=sender,
        receiver=receiver,
        amount=amount,
        nonce=nonce,
        timestamp=datetime.now(UTC),
    )


def test_restore_when_no_snapshot_exists(tmp_path):

    ledger = Ledger()

    replay = ReplayEngine(
        ledger,
        SnapshotStore(tmp_path),
    )

    snapshot = replay.restore_from_snapshot()

    assert snapshot is None

    assert ledger.balances == {}
    assert ledger.nonces == {}
    assert ledger.processed_ids == set()


def test_restore_balances(tmp_path):

    original = Ledger()

    original.balances = {
        "Alice": 150,
        "Bob": 20,
    }

    store = SnapshotStore(tmp_path)

    store.save_snapshot(
        original,
        snapshot_id=1,
        last_hash="abc",
        journal_position=5,
    )

    restored = Ledger()

    replay = ReplayEngine(
        restored,
        store,
    )

    replay.restore_from_snapshot()

    assert restored.balances == original.balances


def test_restore_nonces(tmp_path):

    original = Ledger()

    original.nonces = {
        "Alice": 7,
        "Bob": 3,
    }

    store = SnapshotStore(tmp_path)

    store.save_snapshot(
        original,
        snapshot_id=1,
        last_hash="abc",
        journal_position=10,
    )

    restored = Ledger()

    ReplayEngine(
        restored,
        store,
    ).restore_from_snapshot()

    assert restored.nonces == original.nonces


def test_restore_processed_ids(tmp_path):

    original = Ledger()

    original.processed_ids = {
        "1",
        "2",
        "3",
    }

    store = SnapshotStore(tmp_path)

    store.save_snapshot(
        original,
        snapshot_id=1,
        last_hash="abc",
        journal_position=3,
    )

    restored = Ledger()

    ReplayEngine(
        restored,
        store,
    ).restore_from_snapshot()

    assert restored.processed_ids == original.processed_ids


def test_restore_future_transactions(tmp_path):

    original = Ledger()

    buffered = tx(
        "5",
        "Alice",
        "Bob",
        20,
        5,
    )

    original.future_transactions = {
        "Alice": {
            5: buffered,
        }
    }

    store = SnapshotStore(tmp_path)

    store.save_snapshot(
        original,
        snapshot_id=1,
        last_hash="abc",
        journal_position=4,
    )

    restored = Ledger()

    ReplayEngine(
        restored,
        store,
    ).restore_from_snapshot()

    assert "Alice" in restored.future_transactions

    promoted = restored.future_transactions["Alice"][5]

    assert promoted.tx_id == "5"
    assert promoted.amount == 20


def test_restore_returns_snapshot(tmp_path):

    ledger = Ledger()

    store = SnapshotStore(tmp_path)

    store.save_snapshot(
        ledger,
        snapshot_id=123,
        last_hash="hash",
        journal_position=8,
    )

    replay = ReplayEngine(
        Ledger(),
        store,
    )

    snapshot = replay.restore_from_snapshot()

    assert snapshot.snapshot_id == 123
    assert snapshot.journal_position == 8


def test_restore_full_state(tmp_path):

    original = Ledger()

    original.balances = {"Alice": 100}
    original.nonces = {"Alice": 2}
    original.processed_ids = {"1", "2"}

    buffered = tx(
        "3",
        "Alice",
        "Bob",
        20,
        3,
    )

    original.future_transactions = {
        "Alice": {
            3: buffered,
        }
    }

    store = SnapshotStore(tmp_path)

    store.save_snapshot(
        original,
        snapshot_id=1,
        last_hash="abc",
        journal_position=2,
    )

    restored = Ledger()

    ReplayEngine(
        restored,
        store,
    ).restore_from_snapshot()

    assert restored.balances == original.balances
    assert restored.nonces == original.nonces
    assert restored.processed_ids == original.processed_ids
    assert restored.future_transactions["Alice"][3].tx_id == "3"
