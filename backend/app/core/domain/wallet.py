from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class WalletType(str, Enum):
    """Kind of money a wallet holds.

    CASH    — physical/held money
    DIGITAL — bank accounts, e-wallets, digital money
    SAVINGS — money set aside (family savings, marriage savings, ...)
    CREDIT  — credit cards / credit lines
    OTHER   — anything else
    """
    CASH = "cash"
    DIGITAL = "digital"
    SAVINGS = "savings"
    CREDIT = "credit"
    OTHER = "other"


@dataclass
class Wallet:
    user_id: UUID
    name: str
    type: WalletType = WalletType.CASH
    currency: str = "JOD"
    balance: Decimal = Decimal("0")
    initial_balance: Decimal = Decimal("0")
    icon: str | None = None
    is_active: bool = True
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
