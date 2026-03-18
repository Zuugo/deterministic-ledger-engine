def test_recovery(system, tx_factory):
    processor, ledger = system

    processor.process(tx_factory(1, "SYSTEM", "Alice", 100, 1))
    processor.process(tx_factory(1, "ALICE", "Bob", 30, 1))

    before = dict(ledger.balances)

    # simulate restart
    processor2, ledger2 = system

    after = dict(ledger2.balances)

    assert before == after
