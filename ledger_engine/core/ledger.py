from ledger_engine.exceptions.exceptions import (
    DuplicateTransactionError,
    FutureNonceError,
    InsufficientBalanceError,
    InvalidNonceError,
)
from ledger_engine.models.transaction import Transaction


class Ledger:

    def __init__(self):

        self.balances: dict[str, int] = {}
        self.nonces: dict[str, int] = {}
        self.processed_ids: set[str] = set()
        self.future_transactions: dict[str, dict[int, Transaction]] = {}

    def apply_transaction(self, tx: Transaction) -> bool:
        if tx.tx_id in self.processed_ids:
            raise DuplicateTransactionError()

        expected = self.nonces.get(tx.sender, 0) + 1

        if tx.nonce < expected:
            raise InvalidNonceError()

        if tx.nonce > expected:
            self.future_transactions.setdefault(tx.sender, {})[tx.nonce] = tx
            raise FutureNonceError()

        # nonce == expected

        if tx.sender == "SYSTEM":
            if not tx.receiver:
                return False
        else:
            sender_balance = self.balances.get(tx.sender, 0)

            if sender_balance < tx.amount:
                raise InsufficientBalanceError()

            self.balances[tx.sender] = sender_balance - tx.amount

        if tx.receiver:
            self.balances[tx.receiver] = self.balances.get(tx.receiver, 0) + tx.amount

        self.nonces[tx.sender] = tx.nonce

        self.processed_ids.add(tx.tx_id)

        return True

    """
    def process_buffer(self, sender: str):
        expected = self.nonces.get(sender, 0) + 1
        sender_buffer = self.future_transactions.get(sender, {})

        while expected in sender_buffer:
            tx = sender_buffer.pop(expected)
            self.apply_transaction(tx)

            expected = self.nonces.get(sender, 0) + 1

        if not sender_buffer: 
            self.future_transactions.pop(sender, None)

    """

    def get_balances(self):
        return dict(self.balances)

    def get_processable_buffered(self, sender: str):
        expected = self.nonces.get(sender, 0) + 1

        sender_buffer = self.future_transactions.get(sender, {})

        if expected in sender_buffer:
            return sender_buffer.pop(expected)

        return None
