from decimal import Decimal

from pydantic import BaseModel

VALID_CATEGORIES = ["Food", "Transport", "Housing", "Utilities", "Entertainment",
                    "Shopping", "Health", "Education", "Income", "Savings", "Other"]


class TransactionProposal(BaseModel):
    amount_original: Decimal
    currency_original: str
    description: str
    category: str
    confidence: float
    transaction_date: str | None = None  # ISO 8601 date, optional


class SpendingContext(BaseModel):
    category: str
    this_month_total: Decimal
    transaction_count: int


class WhisperResponse(BaseModel):
    proposal_id: str
    proposal: TransactionProposal
    persona_message: str
    spending_context: SpendingContext | None = None


class AgentRequest(BaseModel):
    message: str
