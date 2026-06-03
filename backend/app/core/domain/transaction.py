from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.core.exceptions import ValidationError

VALID_CURRENCIES = frozenset({"JOD", "USD"})

# Maximum precision for monetary values as required by the domain.
# Using DECIMAL(18,6) in the DB; domain layer enforces the same.
MONETARY_PRECISION = Decimal("0.000001")


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
    is_deleted: bool = False
    wallet_id: UUID | None = None
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
        if errors:
            raise ValidationError("; ".join(errors))

    @staticmethod
    def compute_base_amount(
        amount_original: Decimal,
        currency_original: str,
        exchange_rate: Decimal,
    ) -> Decimal:
        if currency_original == "JOD":
            return amount_original
        return (amount_original * exchange_rate).quantize(MONETARY_PRECISION)
