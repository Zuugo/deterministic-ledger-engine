import json
import queue
from pathlib import Path

from ledger_engine.models.transaction import Transaction


class PersistentTransactionQueue:

    def __init__(self, path="data/queue.log"):
        self.q = queue.PriorityQueue()
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self._load()

    def enqueue(self, item):
        self.q.put((item["next_attempt"], item))

        serializable_item = {
            "tx": item["tx"].__dict__,
            "retries": item["retries"],
            "next_attempt": item["next_attempt"],
        }

    #  with open(self.path, "a") as f:
    #     f.write(json.dumps(serializable_item) + "\n")

    def dequeue(self):
        _, item = self.q.get()
        return item

    def is_empty(self):
        return self.q.empty()

    def _load(self):
        if not self.path.exists():
            return

        with open(self.path, "r") as f:
            for line in f:
                data = json.loads(line.strip())

                tx = Transaction(**data["tx"])

                item = {
                    "tx": tx,
                    "retries": data["retries"],
                    "next_attempt": data["next_attempt"],
                }
                self.q.put((item["next_attempt"], item))
