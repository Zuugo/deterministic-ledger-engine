from datetime import UTC, datetime

from ledger_engine.core.ledger import Ledger
from ledger_engine.models.transaction import Transaction
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


def test_save_and_load_snapshot(tmp_path):
    ledger = Ledger()

    ledger.balances = {
        "Alice": 100,
        "Bob": 50,
    }

    ledger.nonces = {
        "Alice": 3,
    }

    ledger.processed_ids = {
        "1",
        "2",
    }

    store = SnapshotStore(tmp_path)

    store.save_snapshot(
        ledger,
        snapshot_id=123,
        last_hash="abc123",
        journal_position=2,
    )

    snapshot = store.load_latest_snapshot()

    assert snapshot.snapshot_id == 123
    assert snapshot.last_hash == "abc123"
    assert snapshot.journal_position == 2

    assert snapshot.balances == ledger.balances
    assert snapshot.nonces == ledger.nonces
    assert set(snapshot.processed_ids) == ledger.processed_ids


def test_future_transactions_restored(tmp_path):
    ledger = Ledger()

    buffered = tx(
        "5",
        "Alice",
        "Bob",
        20,
        5,
    )

    ledger.future_transactions = {
        "Alice": {
            5: buffered,
        }
    }

    store = SnapshotStore(tmp_path)

    store.save_snapshot(
        ledger,
        snapshot_id=1,
        last_hash="hash",
        journal_position=10,
    )

    snapshot = store.load_latest_snapshot()

    restored = snapshot.future_transactions["Alice"][5]

    assert restored.tx_id == "5"
    assert restored.amount == 20
    assert restored.nonce == 5


def test_snapshot_is_independent_of_ledger(tmp_path):
    ledger = Ledger()

    ledger.balances["Alice"] = 100

    store = SnapshotStore(tmp_path)

    store.save_snapshot(
        ledger,
        snapshot_id=1,
        last_hash="hash",
        journal_position=1,
    )

    ledger.balances["Alice"] = 500

    snapshot = store.load_latest_snapshot()

    assert snapshot.balances["Alice"] == 100


def test_latest_snapshot_loaded(tmp_path):
    ledger = Ledger()

    store = SnapshotStore(tmp_path)

    store.save_snapshot(
        ledger,
        snapshot_id=1,
        last_hash="h1",
        journal_position=1,
    )

    store.save_snapshot(
        ledger,
        snapshot_id=2,
        last_hash="h2",
        journal_position=2,
    )

    snapshot = store.load_latest_snapshot()

    assert snapshot.snapshot_id == 2


def test_load_when_no_snapshot_exists(tmp_path):
    store = SnapshotStore(tmp_path)

    assert store.load_latest_snapshot() is None


def test_checksum_file_created(tmp_path):
    ledger = Ledger()

    store = SnapshotStore(tmp_path)

    store.save_snapshot(
        ledger,
        snapshot_id=99,
        last_hash="hash",
        journal_position=3,
    )

    checksum = tmp_path / "snapshot_99.sha256"

    assert checksum.exists()


def test_snapshot_file_created(tmp_path):
    ledger = Ledger()

    store = SnapshotStore(tmp_path)

    store.save_snapshot(
        ledger,
        snapshot_id=77,
        last_hash="hash",
        journal_position=5,
    )

    snapshot = tmp_path / "snapshot_77.json"

    assert snapshot.exists()
