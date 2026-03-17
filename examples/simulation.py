import time

from ledger_engine.core.ledger import Ledger
from ledger_engine.execution.processor import TransactionProcessor
from ledger_engine.models.transaction import Transaction
from ledger_engine.replay.replay_engine import ReplayEngine
from ledger_engine.storage.snapshot_store import SnapshotStore
from ledger_engine.storage.transaction_journal import TransactionJournal
from ledger_engine.validation.validator import TransactionValidator


def create_processor():
    ledger = Ledger()

    journal = TransactionJournal("data/journal.log")
    snapshot_store = SnapshotStore("data/snapshot.json")

    replay_engine = ReplayEngine(ledger, snapshot_store)

    validator = TransactionValidator()

    processor = TransactionProcessor(
        ledger=ledger,
        journal=journal,
        snapshot_store=snapshot_store,
        replay_engine=replay_engine,
        validate=validator,
        snapshot_interval=5,
    )

    processor.start()

    return processor, ledger


def tx(tx_id: str, sender: str, receiver: str, amount: int, nonce: int):
    return Transaction(
        tx_id=tx_id,
        sender=sender,
        receiver=receiver,
        amount=amount,
        nonce=nonce,
        timestamp=time.time(),
    )


def submit(processor, tx):
    print(f"\nProcessing {tx.sender} -> {tx.receiver} | {tx.amount} | {tx.nonce}")
    success = processor.process(tx)
    print("SUCCESS" if success else "FAILED")


def print_balances(ledger):
    print("\nBalances")
    print("--------")

    for account, balance in ledger.get_balances().items():
        print(account, balance)


if __name__ == "__main__":
    print("\n===SYSTEM START===")

    processor, ledger = create_processor()

    # Mint
    submit(processor, tx("1", "SYSTEM", "Alice", 100, 1))
    submit(processor, tx("2", "SYSTEM", "Bob", 50, 2))

    # Normal transaction
    submit(processor, tx("3", "Alice", "Bob", 20, 1))

    # Future transaction
    submit(processor, tx("4", "Alice", "Bob", 10, 3))
    submit(processor, tx("5", "Alice", "Bob", 20, 2))

    print_balances(ledger)

    print("\n***SYSTEM CRASH***")

    # simulate crash

    processor = None
    ledger = None

    print("\n===SYSTEM RESTART===")

    processor, ledger = create_processor()

    print_balances(ledger)
