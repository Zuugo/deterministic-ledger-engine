from ledger_engine.models.transaction import Transaction


class TransactionValidator:

    def validate(self, tx: Transaction) -> bool:

        if not tx.tx_id:
            return False

        if not tx.sender:
            return False

        if tx.amount <= 0:
            return False

        if tx.sender == tx.receiver:
            return False

        if tx.nonce <= 0:
            return False

        return True
