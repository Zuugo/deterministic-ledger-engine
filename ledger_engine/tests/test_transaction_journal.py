import json
from datetime import UTC, datetime

import pytest

from ledger_engine.exceptions.exceptions import JournalCorruptionError
from ledger_engine.models.transaction import Transaction
from ledger_engine.storage.transaction_journal import TransactionJournal


def tx(tx_id, sender, receiver, amount, nonce):
    return Transaction(
        tx_id=tx_id,
        sender=sender,
        receiver=receiver,
        amount=amount,
        nonce=nonce,
        timestamp=datetime.now(UTC),
    )


def test_append_and_load(tmp_path):

    journal = TransactionJournal(tmp_path / "journal.log")

    t1 = tx("1", "SYSTEM", "Alice", 100, 1)
    t2 = tx("2", "Alice", "Bob", 25, 1)

    journal.append(t1)
    journal.append(t2)

    loaded = journal.load_from(0)

    assert len(loaded) == 2

    assert loaded[0].tx_id == "1"
    assert loaded[1].tx_id == "2"

    assert loaded[1].sender == "Alice"
    assert loaded[1].receiver == "Bob"


def test_get_position(tmp_path):

    journal = TransactionJournal(tmp_path / "journal.log")

    assert journal.get_position() == 0

    journal.append(tx("1", "SYSTEM", "Alice", 100, 1))
    journal.append(tx("2", "Alice", "Bob", 10, 1))

    assert journal.get_position() == 2


def test_previous_hash_chain(tmp_path):

    journal = TransactionJournal(tmp_path / "journal.log")

    journal.append(tx("1", "SYSTEM", "Alice", 100, 1))
    journal.append(tx("2", "Alice", "Bob", 20, 1))

    with open(journal.path) as f:
        lines = [json.loads(line) for line in f]

    assert lines[0]["previous_hash"] == "GENESIS"

    assert lines[1]["previous_hash"] == lines[0]["hash"]


def test_checksum_corruption_detected(tmp_path):

    journal = TransactionJournal(tmp_path / "journal.log")

    journal.append(tx("1", "SYSTEM", "Alice", 100, 1))

    with open(journal.path) as f:
        record = json.loads(f.readline())

    record["amount"] = 99999

    with open(journal.path, "w") as f:
        f.write(json.dumps(record) + "\n")

    with pytest.raises(JournalCorruptionError):
        journal.load_from(0)


def test_hash_corruption_detected(tmp_path):

    journal = TransactionJournal(tmp_path / "journal.log")

    journal.append(tx("1", "SYSTEM", "Alice", 100, 1))

    with open(journal.path) as f:
        record = json.loads(f.readline())

    record["hash"] = "BAD_HASH"

    with open(journal.path, "w") as f:
        f.write(json.dumps(record) + "\n")

    with pytest.raises(JournalCorruptionError):
        journal.load_from(0)


def test_load_from_position(tmp_path):

    journal = TransactionJournal(tmp_path / "journal.log")

    for i in range(5):
        journal.append(
            tx(
                str(i),
                "SYSTEM",
                "Alice",
                10,
                i + 1,
            )
        )

    loaded = journal.load_from(3)

    assert len(loaded) == 2

    assert loaded[0].tx_id == "3"
    assert loaded[1].tx_id == "4"


def test_load_after_hash(tmp_path):

    journal = TransactionJournal(tmp_path / "journal.log")

    for i in range(3):
        journal.append(
            tx(
                str(i),
                "SYSTEM",
                "Alice",
                10,
                i + 1,
            )
        )

    with open(journal.path) as f:
        records = [json.loads(line) for line in f]

    second_hash = records[1]["hash"]

    loaded = journal.load_after_hash(second_hash)

    assert len(loaded) == 1
    assert loaded[0].tx_id == "2"
