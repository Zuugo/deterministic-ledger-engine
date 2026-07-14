from dataclasses import dataclass

from ledger_engine.models.transaction import Transaction


@dataclass(slots=True)
class Snapshot:

    snapshot_id: int

    journal_position: int

    last_hash: str

    balances: dict[str, int]

    nonces: dict[str, int]

    processed_ids: list[str]

    future_transactions: dict[str, dict[int, Transaction]]

    def restore(self, ledger):
        ledger.balances = self.balances.copy()
        ledger.nonces = self.nonces.copy()
        ledger.processed_ids = set(self.processed_ids)
        ledger.future_transactions = self.future_transactions.copy()
