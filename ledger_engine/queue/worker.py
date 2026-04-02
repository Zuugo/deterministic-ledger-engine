import threading
import time


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
        while self.running:
            if not self.queue.is_empty():
                tx = self.queue.dequeue()

                success, reason = self.processor.process(tx)

                if not success:
                    print(f"[WORKER ERROR] {reason}")
