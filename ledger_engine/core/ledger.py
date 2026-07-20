from ledger_engine.exceptions.exceptions import (
    DuplicateTransactionError,
    FutureNonceError,
    InsufficientBalanceError,
    InvalidNonceError,
)
from ledger_engine.models.transaction import Transaction


class Ledger:
    SYSTEM_ACCOUNT = "SYSTEM"
    MAX_FUTURE_NONCE_GAP = 10

    def __init__(self):
        self.balances: dict[str, int] = {}
        self.nonces: dict[str, int] = {}
        self.processed_ids: set[str] = set()
        self.future_transactions: dict[str, dict[int, Transaction]] = {}

    def apply_transaction(self, tx: Transaction) -> bool:
        self._validate_duplicate(tx)
        self._validate_nonce(tx)
        self._apply_transfer(tx)
        self._finalize_transaction(tx)
        return True

    def get_balances(self) -> dict[str, int]:
        return dict(self.balances)

    def expected_nonce(self, sender: str) -> int:
        return self.nonces.get(sender, 0) + 1

    def pop_processable_buffered(self, sender: str) -> Transaction | None:
        expected_nonce = self.expected_nonce(sender)

        sender_buffer = self.future_transactions.get(sender, {})

        if expected_nonce not in sender_buffer:
            return None

        tx = sender_buffer.pop(expected_nonce)

        if not sender_buffer:
            self.future_transactions.pop(sender, None)

        return tx

    def _validate_duplicate(self, tx: Transaction) -> None:
        if tx.tx_id in self.processed_ids:
            raise DuplicateTransactionError()

    def _validate_nonce(self, tx: Transaction) -> None:
        expected_nonce = self.expected_nonce(tx.sender)

        if tx.nonce < expected_nonce:
            raise InvalidNonceError()

        if tx.nonce > expected_nonce + self.MAX_FUTURE_NONCE_GAP:
            raise InvalidNonceError()

        if tx.nonce > expected_nonce:
            self._buffer_transaction(tx)
            raise FutureNonceError()

    def _buffer_transaction(self, tx: Transaction) -> None:
        self.future_transactions.setdefault(tx.sender, {})[tx.nonce] = tx

    def _apply_transfer(self, tx: Transaction):

        if self._is_system_transaction(tx):

            if not tx.receiver:
                raise ValueError("SYSTEM transaction requires receiver")

        else:

            sender_balance = self.balances.get(tx.sender, 0)

            if sender_balance < tx.amount:
                raise InsufficientBalanceError()

            self.balances[tx.sender] = sender_balance - tx.amount

        if tx.receiver:
            self.balances[tx.receiver] = self.balances.get(tx.receiver, 0) + tx.amount

    def _finalize_transaction(self, tx: Transaction) -> None:
        self.nonces[tx.sender] = tx.nonce
        self.processed_ids.add(tx.tx_id)

    @staticmethod
    def _is_system_transaction(tx: Transaction) -> bool:
        return tx.sender == Ledger.SYSTEM_ACCOUNT
