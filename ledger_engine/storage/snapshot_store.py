import copy
import hashlib
import json
from pathlib import Path

from ledger_engine.storage.snapshot_checksum import SnapshotChecksum
from ledger_engine.storage.snapshot_serializer import SnapshotSerializer


class SnapshotStore:

    def __init__(self, directory="snapshot"):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def save_snapshot(
        self,
        ledger,
        snapshot_id,
        last_hash,
        journal_position,
    ):

        snapshot = SnapshotSerializer.serialize(
            ledger,
            snapshot_id,
            last_hash,
            journal_position,
        )

        snapshot_json = json.dumps(
            snapshot,
            indent=2,
            sort_keys=True,
        )

        checksum = SnapshotChecksum.calculate(snapshot_json)

        snapshot_file = self.directory / f"snapshot_{snapshot_id}.json"

        checksum_file = self.directory / f"snapshot_{snapshot_id}.sha256"

        snapshot_file.write_text(snapshot_json)
        checksum_file.write_text(checksum)

    def load_latest_snapshot(self):

        snapshots = sorted(
            self.directory.glob("snapshot_*.json"),
            key=lambda p: int(p.stem.split("_")[1]),
        )

        if not snapshots:
            return None

        latest = snapshots[-1]

        with open(latest) as f:
            return json.load(f)
