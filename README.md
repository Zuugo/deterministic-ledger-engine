Deterministic Ledger Engine

A backend-focused transaction processing engine designed to simulate financial-grade systems with strong guarantees
around consistency, recovery and correctness.

---

Features

    - Deterministic transaction execution
    - Nonce-based ordering system
    - Idempotent processing (safe retries)
    - Write-Ahead Log (journal)
    - Snapshot based recovery
    - Crash recovery support
    - Concurrency safe processing
    - Comprehensive test suite

Why This Project?

This project demonstrates how real-world financial systems handle:

    - Transaction ordering
    - Fault tolerance
    - Data recovery
    - System consistency under failure
    - Concurrent processing

Architecture

See architecture.md for full system design

Testing

The system includes a robust test suite covering:

    - Recovery after crash
    - Duplicate transaction handling
    - Out of order transaction buffering
    - Snapshot consistency
    - Concurrency safety
    - Journal corruption handling

Run tests:

    pytest

Example Usage

    python -m examples.simulation

Tech Stack

    - Python 3.12
    - pytest
    - File-based persistence (JSON, WAL)

---

Focus

This project focuses strictly on backend/system design and intentionally excludes frontend components.

Future Work

    - API integration (Django)
    - Distribution transaction processing
    - Queue-based architecture
    - ML-based anomally

---

Author

Backend-focused engineer building systems with strong guarantees around correctness and reliability.
