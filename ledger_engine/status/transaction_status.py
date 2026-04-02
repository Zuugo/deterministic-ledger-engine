class TransactionStatusStore:

    def __init__(self):
        self.store = {}

    def set_status(self, tx_id, status, reason=None):
        self.store[tx_id] = {
            "status": status,
            "reason": reason,
        }

    def get_status(self, tx_id):
        return self.store.get(tx_id, {"status": "UNKNOWN"})

