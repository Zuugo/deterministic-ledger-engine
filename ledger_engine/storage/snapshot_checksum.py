import hashlib


class SnapshotChecksum:

    @staticmethod
    def calculate(snapshot_json: str) -> str:
        return hashlib.sha256(snapshot_json.encode()).hexdigest()

    @staticmethod
    def verify(snapshot_json: str, expected_checksum: str) -> None:
        actual = SnapshotChecksum.calculate(snapshot_json)

        if actual != expected_checksum:
            raise ValueError("Snapshot checksum verification failed.")
