from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Transaction:
    tx_id: str
    sender: str
    receiver: Optional[str]
    amount: int
    nonce: int
    timestamp: float
