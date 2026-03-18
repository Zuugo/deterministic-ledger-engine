def test_journal_corruption(system, tx_factory):
    processor, ledger = system

    processor.process(tx_factory(1, "SYSTEM", "Alice", 100, 1))

    # corrupt journal

    with open("data/journal.log", "a") as f:
        f.write("INVALID_JSON\n")

    # restart system

    processor2, ledger2 = system

    assert ledger2.balances["Alice"] == 100
