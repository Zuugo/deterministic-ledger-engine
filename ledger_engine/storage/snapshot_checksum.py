import hashlib


class SnapshotChecksum:

    @staticmethod
    def calculate(snapshot_json: str) -> str:
        return hashlib.sha256(snapshot_json.encode()).hexdigest()
