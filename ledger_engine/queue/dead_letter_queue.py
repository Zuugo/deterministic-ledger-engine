

class DeadLetterQueue:
    def __init__(self):
        self.failed = []

    def add(self, item, reason):
        self.failed.append({
            "item": item,
            "reason": reason
        })

    def get_all(self):
        return self.failed
