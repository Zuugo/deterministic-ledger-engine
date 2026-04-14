import threading
import time

from ledger.shared.state import dlq, status_store


class TransactionWorker:

    def __init__(self, queue, processor):
        self.queue = queue
        self.processor = processor
        self.running = False

    def start(self):
        self.running = True
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()

    def run(self):
        MAX_RETRIES = 3
        while self.running:
            if not self.queue.is_empty():
                item = self.queue.dequeue()

                now = time.time()

                if item["next_attempt"] > now:
                    self.queue.enqueue(item)
                    continue

                tx = item["tx"]
                retries = item["retries"]

                success, reason = self.processor.process(tx)

                if success:
                    status_store.set_status(tx.tx_id, "SUCCESS")
                else:
                    if retries < MAX_RETRIES:
                        delay = 2**retries
                        print(f"[SCHEDULE RETRY] {tx.tx_id} in {delay}s")

                        item["retries"] += 1
                        item["next_attempt"] = time.time() + delay
                        self.queue.enqueue(item)

                    else:
                        print(f"[DLQ] {tx.tx_id} failed permanently")

                        dlq.add(item, reason)
                        status_store.set_status(tx.tx_id, "FAILED", reason)
            else:
                time.sleep(0.01)
