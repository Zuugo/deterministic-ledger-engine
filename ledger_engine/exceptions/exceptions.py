class LedgerError(Exception):
    pass


class DuplicateTransactionError(LedgerError):
    def __str__(self):
        return "Duplicate transaction"


class InsufficientBalanceError(LedgerError):
    def __str__(self):
        return "Insufficient balance"


class FutureNonceError(LedgerError):
    def __str__(self):
        return "Future nonce (buffered)"


class InvalidNonceError(LedgerError):
    def __str__(self):
        return "Nonce too low"
