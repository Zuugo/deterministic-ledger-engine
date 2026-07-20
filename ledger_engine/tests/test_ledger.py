from datetime import UTC, datetime

import pytest

from ledger_engine.core.ledger import Ledger
from ledger_engine.exceptions.exceptions import (
    DuplicateTransactionError,
    FutureNonceError,
    InsufficientBalanceError,
    InvalidNonceError,
)
from ledger_engine.models.transaction import Transaction


def tx(
    tx_id: str,
    sender: str,
    receiver: str,
    amount: int,
    nonce: int,
):
    return Transaction(
        tx_id=tx_id,
        sender=sender,
        receiver=receiver,
        amount=amount,
        nonce=nonce,
        timestamp=datetime.now(UTC),
    )


def test_system_mint():

    ledger = Ledger()

    ledger.apply_transaction(
        tx(
            "1",
            "SYSTEM",
            "Alice",
            100,
            1,
        )
    )

    assert ledger.balances["Alice"] == 100


def test_transfer():

    ledger = Ledger()

    ledger.apply_transaction(tx("1", "SYSTEM", "Alice", 100, 1))

    ledger.apply_transaction(tx("2", "Alice", "Bob", 40, 1))

    assert ledger.balances["Alice"] == 60
    assert ledger.balances["Bob"] == 40


def test_duplicate_transaction():

    ledger = Ledger()

    transaction = tx(
        "1",
        "SYSTEM",
        "Alice",
        100,
        1,
    )

    ledger.apply_transaction(transaction)

    with pytest.raises(DuplicateTransactionError):
        ledger.apply_transaction(transaction)


def test_invalid_nonce():

    ledger = Ledger()

    ledger.apply_transaction(tx("1", "SYSTEM", "Alice", 100, 1))

    ledger.apply_transaction(tx("2", "Alice", "Bob", 20, 1))

    with pytest.raises(InvalidNonceError):
        ledger.apply_transaction(tx("3", "Alice", "Bob", 20, 1))


def test_future_nonce_buffered():

    ledger = Ledger()

    ledger.apply_transaction(tx("1", "SYSTEM", "Alice", 100, 1))

    with pytest.raises(FutureNonceError):
        ledger.apply_transaction(tx("2", "Alice", "Bob", 20, 3))

    assert "Alice" in ledger.future_transactions
    assert 3 in ledger.future_transactions["Alice"]


def test_insufficient_balance():

    ledger = Ledger()

    ledger.apply_transaction(tx("1", "SYSTEM", "Alice", 100, 1))

    with pytest.raises(InsufficientBalanceError):
        ledger.apply_transaction(tx("2", "Alice", "Bob", 200, 1))


def test_buffer_promotion():

    ledger = Ledger()

    ledger.apply_transaction(tx("1", "SYSTEM", "Alice", 100, 1))

    with pytest.raises(FutureNonceError):
        ledger.apply_transaction(tx("2", "Alice", "Bob", 20, 3))

    with pytest.raises(FutureNonceError):
        ledger.apply_transaction(tx("3", "Alice", "Bob", 20, 2))

    ledger.apply_transaction(tx("4", "Alice", "Bob", 20, 1))

    promoted = ledger.pop_processable_buffered("Alice")

    assert promoted is not None
    assert promoted.tx_id == "3"
    assert promoted.nonce == 2


def test_nonce_outside_future_window():

    ledger = Ledger()

    ledger.apply_transaction(tx("1", "SYSTEM", "Alice", 100, 1))

    with pytest.raises(InvalidNonceError):
        ledger.apply_transaction(tx("2", "Alice", "Bob", 10, 50))
