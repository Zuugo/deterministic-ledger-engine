def test_idempotency(system, tx_factory):
    processor, ledger = system

    t = tx_factory(1, "SYSTEM", "Alice", 100, 1)

    assert processor.process(t) is True
    assert processor.process(t) is True

    assert ledger.balances["Alice"] == 100
