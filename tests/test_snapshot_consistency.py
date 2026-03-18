def test_snapshot_consistency(system, tx_factory):
    processor, ledger = system

    for i in range(1, 6):
        processor.process(tx_factory(i, "SYSTEM", "Alice", 10, i))

    snapshot_balance = dict(ledger.balances)

    # restart

    processor2, ledger2 = system

    assert ledger2.balances == snapshot_balance
