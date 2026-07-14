from dataclasses import dataclass, field

from ledger_engine.models.transaction import Transaction


@dataclass
class ProcessResult:

    success: bool

    reason: str | None = None

    retryable: bool = False

    journal_position: int = 0

    snapshot_created: bool = False

    snapshot_id: int | None = None

    promoted_transactions: list[Transaction] = field(default_factory=list)
