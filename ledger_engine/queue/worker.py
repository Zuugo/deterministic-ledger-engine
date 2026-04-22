import threading
import time

import django

django.setup()

from ledger.models import TransactionStatus
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
                    time.sleep(0.01)
                    continue

                tx = item["tx"]
                retries = item["retries"]

                success, reason = self.processor.process(tx)

                if success:
                    TransactionStatus.objects.update_or_create(
                        tx_id=tx.tx_id, defaults={"status": "SUCCESS", "reason": None}
                    )
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
                        TransactionStatus.objects.update_or_create(
                            tx_id=tx.tx_id,
                            defaults={"status": "FAILED", "reason": reason},
                        )
                        continue
            else:
                time.sleep(0.01)
