from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from app.core.exceptions import ValidationError

VALID_CURRENCIES = frozenset({"JOD", "USD"})

# Maximum precision for monetary values as required by the domain.
# Using DECIMAL(18,6) in the DB; domain layer enforces the same.
MONETARY_PRECISION = Decimal("0.000001")


class TransactionType(str, Enum):
    """Direction of a transaction relative to its wallet.

    EXPENSE      — money leaving a wallet (subtracts from balance)
    INCOME       — money entering a wallet (adds to balance)
    TRANSFER_OUT — outgoing leg of an inter-wallet transfer (subtracts)
    TRANSFER_IN  — incoming leg of an inter-wallet transfer (adds)
    """
    EXPENSE = "expense"
    INCOME = "income"
    TRANSFER_OUT = "transfer_out"
    TRANSFER_IN = "transfer_in"


TRANSFER_TYPES = frozenset({TransactionType.TRANSFER_OUT.value, TransactionType.TRANSFER_IN.value})


@dataclass(frozen=True)
class ExchangeRate:
    date: date
    jod_per_usd: Decimal
    source: str = "manual"

    def __post_init__(self) -> None:
        if self.jod_per_usd <= 0:
            raise ValidationError(
                "Exchange rate must be positive",
                {"jod_per_usd": str(self.jod_per_usd)},
            )


@dataclass
class Transaction:
    user_id: UUID
    amount_original: Decimal
    currency_original: str
    category: str
    transaction_date: date
    amount_base: Decimal
    exchange_rate: Decimal = Decimal("1.0")
    description: str | None = None
    source: str = "manual"
    type: TransactionType = TransactionType.EXPENSE
    is_deleted: bool = False
    wallet_id: UUID | None = None
    transfer_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        errors: list[str] = []
        if self.amount_original <= 0:
            errors.append("amount_original must be positive")
        if self.currency_original not in VALID_CURRENCIES:
            errors.append(f"currency_original must be one of {VALID_CURRENCIES}")
        if self.amount_base <= 0:
            errors.append("amount_base must be positive")
        if self.exchange_rate <= 0:
            errors.append("exchange_rate must be positive")
        if self.is_transfer and self.transfer_id is None:
            errors.append("transfer transactions must carry a transfer_id")
        if errors:
            raise ValidationError("; ".join(errors))

    @property
    def is_transfer(self) -> bool:
        return self.type in (TransactionType.TRANSFER_OUT, TransactionType.TRANSFER_IN)

    @property
    def signed_amount_base(self) -> Decimal:
        """Effect of this transaction on its wallet balance (JOD base)."""
        if self.type in (TransactionType.INCOME, TransactionType.TRANSFER_IN):
            return self.amount_base
        return -self.amount_base

    @staticmethod
    def compute_base_amount(
        amount_original: Decimal,
        currency_original: str,
        exchange_rate: Decimal,
    ) -> Decimal:
        if currency_original == "JOD":
            return amount_original
        return (amount_original * exchange_rate).quantize(MONETARY_PRECISION)
