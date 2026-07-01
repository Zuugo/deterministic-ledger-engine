import copy
import hashlib
import json
from pathlib import Path

from ledger_engine.core.ledger import Ledger


class SnapshotStore:

    def __init__(self, directory: str = "snapshot"):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def save_snapshot(
        self, ledger: Ledger, snapshot_id: int, last_hash: str, journal_position: int
    ):
        snapshot = {
            "snapshot_id": snapshot_id,
            "journal_position": journal_position,
            "last_hash": last_hash,
            "balances": copy.deepcopy(ledger.balances),
            "nonces": copy.deepcopy(ledger.nonces),
            "processed_ids": list(ledger.processed_ids),
            "future_transactions": {
                sender: {nonce: tx.__dict__ for nonce, tx in txs.items()}
                for sender, txs in ledger.future_transactions.items()
            },
        }

        snapshot_json = json.dumps(snapshot, sort_keys=True, indent=2)

        checksum = hashlib.sha256(snapshot_json.encode()).hexdigest()

        filename = self.directory / f"snapshot_{snapshot['snapshot_id']}.json"

        with open(filename, "w") as f:
            f.write(snapshot_json)

        checksum_path = self.directory / f"snapshot_{snapshot['snapshot_id']}.sha256"

        with open(checksum_path, "w") as f:
            f.write(checksum)

    def load_latest_snapshot(self):
        snapshots = list(self.directory.glob("snapshot_*.json"))

        if not snapshots:
            return None

        latest = max(snapshots, key=lambda p: int(p.stem.split("_")[1]))

        with open(latest, "r") as f:
            print("LOADING SNAPSHOT:", latest)
            print("SNAPSHOT DATA:", snapshots)
            return json.load(f)
