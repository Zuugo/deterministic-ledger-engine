from ledger_engine.models.transaction import Transaction


class Ledger:

    def __init__(self):
        self.transactions: list[Transaction] = []
        self.balances: dict[str, int] = {}
        self.nonces: dict[str, int] = {}
        self.processed_ids: set[str] = set()
        self.future_transactions: dict[str, dict[int, Transaction]] = {}

    def apply_transaction(self, tx: Transaction) -> bool:
        if tx.tx_id in self.processed_ids:
            return False

        expected = self.nonces.get(tx.sender, 0) + 1

        if tx.nonce < expected:
            return False

        if tx.nonce > expected:
            self.future_transactions.setdefault(tx.sender, {})[tx.nonce] = tx
            return False

        # nonce == expected

        if tx.sender == "SYSTEM":
            if not tx.receiver:
                return False
        else:
            sender_balance = self.balances.get(tx.sender, 0)

            if sender_balance < tx.amount:
                return False

            self.balances[tx.sender] = sender_balance - tx.amount

        if tx.receiver:
            self.balances[tx.receiver] = self.balances.get(tx.receiver, 0) + tx.amount

        self.nonces[tx.sender] = tx.nonce
        self.transactions.append(tx)
        self.processed_ids.add(tx.tx_id)

        self.process_buffer(tx.sender)

        return True

    def process_buffer(self, sender: str):
        expected = self.nonces.get(sender, 0) + 1
        sender_buffer = self.future_transactions.get(sender, {})

        while expected in sender_buffer:
            tx = sender_buffer.pop(expected)
            self.apply_transaction(tx)

            expected = self.nonces.get(sender, 0) + 1

        if not sender_buffer:
            self.future_transactions.pop(sender, None)
