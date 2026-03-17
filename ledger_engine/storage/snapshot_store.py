import copy
import json
from pathlib import Path

from ledger_engine.core.ledger import Ledger


class SnapshotStore:

    def __init__(self, directory: str = "snapshot"):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def save_snapshot(self, ledger: Ledger, tx_index: int):
        snapshot = {
            "tx_index": tx_index,
            "balances": copy.deepcopy(ledger.balances),
            "nonces": copy.deepcopy(ledger.nonces),
            "processed_ids": list(ledger.processed_ids),
            "future_transactions": {
                sender: {nonce: tx.__dict__ for nonce, tx in txs.items()}
                for sender, txs in ledger.future_transactions.items()
            },
        }

        filename = self.directory / f"snapshot_{snapshot['tx_index']}.json"

        with open(filename, "w") as f:
            json.dump(snapshot, f, indent=2)

    def load_latest_snapshot(self):
        snapshots = list(self.directory.glob("snapshot_*.json"))

        if not snapshots:
            return None

        latest = max(snapshots, key=lambda p: int(p.stem.split("_")[1]))

        with open(latest, "r") as f:
            print("LOADING SNAPSHOT:", latest)
            print("SNAPSHOT DATA:", snapshots)
            return json.load(f)
