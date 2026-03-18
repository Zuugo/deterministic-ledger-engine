def test_future_transactions_buffering(system, tx_factory):
    processor, ledger = system

    processor.process(tx_factory(1, "SYSTEM", "Alice", 100, 1))

    # future tx
    processor.process(tx_factory(2, "Alice", "Bob", 10, 3))

    # correct order tx
    processor.process(tx_factory(3, "Alice", "Bob", 20, 1))
    processor.process(tx_factory(4, "Alice", "Bob", 30, 2))

    assert ledger.balances["Alice"] == 40
    assert ledger.balances["Bob"] == 60
