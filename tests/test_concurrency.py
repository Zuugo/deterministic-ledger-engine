import threading


def test_concurrent_transactions(system, tx_factory):
    processor, ledger = system

    def worker(i):
        t = tx_factory(1, "SYSTEM", "Alice", 100, i)
        processor.process(t)

    threads = []

    for i in range(1, 11):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    assert ledger.balances["Alice"] == 100
