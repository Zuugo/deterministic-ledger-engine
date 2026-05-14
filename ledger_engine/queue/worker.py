import threading
import time
from datetime import timedelta

import django
from django.db import transaction
from django.utils.timezone import now
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
        TIMEOUT = 10

        print("[WORKER] started.....")

        while self.running:
            current_time = now()

            with transaction.atomic():
                stuck_jobs = TransactionQueue.objects.filter(
                    status="PROCESSING",
                    processing_started_at__lte=current_time
                    - timedelta(seconds=TIMEOUT),
                )

                for stuck in stuck_jobs:
                    print(f"[RECOVERY] Releasing stuck job {stuck.tx_id}")

                    if stuck.retries >= MAX_RETRIES:
                        stuck.status = "FAILED"
                        stuck.reason = "Exceeded retries during recovery"
                        stuck.save()

                        TransactionStatus.objects.update_or_create(
                            tx_id=stuck.tx_id,
                            defaults={"status": "FAILED", "reason": stuck.reason},
                        )

                        print(f"[RECOVERY -> DLQ] {stuck.tx_id}")
                        continue

                    delay = max(1, 2**stuck.retries)

                    stuck.status = "RETRY"
                    stuck.retries += 1
                    stuck.next_attempt = current_time + timedelta(seconds=delay)
                    stuck.save()

                    print(
                        f"[RECOVERY -> RETRY] {stuck.tx_id} in {delay}s (retry={stuck.retries})"
                    )

                job = (
                    TransactionQueue.objects.filter(
                        status__in=["PENDING", "RETRY"], next_attempt__lte=current_time
                    )
                    .order_by("created_at")
                    .first()
                )

                if job:
                    job.status = "PROCESSING"
                    job.processing_started_at = current_time
                    job.save()
            if not job:
                time.sleep(0.5)
                continue

            print(f"[WORKER] Picked job {job.tx_id} (retry={job.retries})")

            tx = Transaction(
                tx_id=job.tx_id,
                sender=job.sender,
                receiver=job.receiver,
                amount=job.amount,
                nonce=job.nonce,
                timestamp=current_time,
            )

            success, reason, retryable = self.processor.process(tx)

            print(
                f"[WORKER] Result for job {job.tx_id}: success={success}, reason={reason}"
            )

            if success:
                job.status = "SUCCESS"
                job.processing_started_at = None
                job.save()

                TransactionStatus.objects.update_or_create(
                    tx_id=job.tx_id, defaults={"status": "SUCCESS", "reason": None}
                )

                print(f"[WORKER] SUCCESS {job.tx_id}")

            else:
                if reason == "Buffered future transaction":
                    job.status = "BUFFERED"
                    job.reason = reason
                    job.processing_started_at = None
                    job.save()

                    TransactionStatus.objects.update_or_create(
                        tx_id=job.tx_id,
                        defaults={
                            "status": "BUFFERED",
                            "reason": reason,
                        },
                    )

                    print(f"[BUFFERED] {job.tx_id}")

                    continue

                elif retryable and job.retries < MAX_RETRIES:
                    delay = max(1, 2**job.retries)

                    job.retries += 1
                    job.next_attempt = current_time + timedelta(seconds=delay)
                    job.status = "RETRY"
                    job.processing_started_at = None
                    job.save()

                    print(f"[SCHEDULE RETRY] {job.tx_id} in {delay}s")

                else:
                    job.status = "FAILED"
                    job.reason = reason
                    job.processing_started_at = None
                    job.save()

                    TransactionStatus.objects.update_or_create(
                        tx_id=job.tx_id,
                        defaults={"status": "FAILED", "reason": reason},
                    )

                    print(f"[DLQ] {job.tx_id} failed permanently")
