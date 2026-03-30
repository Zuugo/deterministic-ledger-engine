class LedgerError(Exception):
    pass


class DuplicateTransactionError(LedgerError):
    def __str__(self):
        return "Duplicate transaction"


class InsufficientBalanceError(LedgerError):
    def __str__(self):
        return "Insufficient balance"


class InvalidNonceError(LedgerError):
    def __str__(self):
        return "Invalid nonce"
