import queue


class TransactionQueue:

    def __init__(self):
        self.q = queue.Queue()

    def enqueue(self, tx):
        self.q.put(tx)

    def dequeue(self):
        return self.q.get()

    def is_empty(self):
        return self.q.empty()
