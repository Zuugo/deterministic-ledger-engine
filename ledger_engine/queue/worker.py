import threading
import time

import django
from django.db import transaction
from ledger.shared.state import dlq, status_store

from ledger_engine.models.transaction import Transaction


class TransactionWorker:

    def __init__(self, queue, processor):
        self.processor = processor
        self.running = False

    def start(self):
        self.running = True
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()

    def run(self):
        from ledger.models import TransactionQueue, TransactionStatus

        MAX_RETRIES = 3

        print("[WORKER] started.....")

        while self.running:
            now = time.time()

            with transaction.atomic():
                job = (
                    TransactionQueue.objects.filter(
                        status__in=["PENDING", "RETRY"], next_attempt__lte=now
                    )
                    .order_by("created_at")
                    .first()
                )

                if job:
                    job.status = "PROCESSING"
                    job.save()

                if not job:
                    time.sleep(0.5)
                    continue

                print(f"[WORKER] Picked job {job.tx_id} (retry={job.retries})")

                job.status = "PROCESSING"
                job.save()

            tx = Transaction(
                tx_id=job.tx_id,
                sender=job.sender,
                receiver=job.receiver,
                amount=job.amount,
                nonce=job.nonce,
                timestamp=now,
            )

            success, reason, retryable = self.processor.process(tx)

            print(
                f"[WORKER] Result for job {job.tx_id}: success={success}, reason={reason}"
            )

            if success:
                job.status = "SUCCESS"
                job.save()

                TransactionStatus.objects.update_or_create(
                    tx_id=job.tx_id, defaults={"status": "SUCCESS", "reason": None}
                )

                print(f"[WORKER] SUCCESS {job.tx_id}")

            else:
                if retryable and job.retries < MAX_RETRIES:
                    delay = max(1, 2**job.retries)

                    job.retries += 1
                    job.next_attempt = time.time() + delay
                    job.status = "RETRY"
                    job.save()

                    print(f"[SCHEDULE RETRY] {job.tx_id} in {delay}s")

                else:
                    job.status = "FAILED"
                    job.reason = reason
                    job.save()

                    TransactionStatus.objects.update_or_create(
                        tx_id=job.tx_id,
                        defaults={"status": "FAILED", "reason": reason},
                    )

                    print(f"[DLQ] {job.tx_id} failed permanently")
