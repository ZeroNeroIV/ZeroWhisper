import csv
import io
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional
from uuid import UUID

from sqlmodel import Session

from app.schemas.transaction import TransactionCreate, VALID_CATEGORIES, VALID_CURRENCIES


TEMPLATE_HEADERS = ["transaction_date", "amount_original", "currency_original", "category", "description"]

# Common bank CSV format header aliases (maps bank column name → our field name)
_HEADER_ALIASES = {
    "date": "transaction_date",
    "trans date": "transaction_date",
    "transaction date": "transaction_date",
    "value date": "transaction_date",
    "amount": "amount_original",
    "debit": "amount_original",
    "credit": "amount_original",
    "currency": "currency_original",
    "ccy": "currency_original",
    "memo": "description",
    "details": "description",
    "narration": "description",
    "particulars": "description",
    "type": "category",
    "trans type": "category",
}


@dataclass
class ImportResult:
    imported: int
    errors: list[dict]  # [{"row": int, "error": str}]


@dataclass
class ParsedRow:
    transaction_date: date
    amount_original: Decimal
    currency_original: str
    category: str
    description: Optional[str]


def _normalize_header(h: str) -> str:
    return h.strip().lower()


def _map_headers(raw_headers: list[str]) -> dict[str, int]:
    """
    Return a mapping of our canonical field names → column index.
    Tries template headers first, then aliases.
    """
    mapping: dict[str, int] = {}
    for idx, raw in enumerate(raw_headers):
        normalized = _normalize_header(raw)
        if normalized in TEMPLATE_HEADERS:
            mapping[normalized] = idx
        elif normalized in _HEADER_ALIASES:
            canonical = _HEADER_ALIASES[normalized]
            if canonical not in mapping:  # don't overwrite already-found canonical
                mapping[canonical] = idx
    return mapping


def _parse_date(s: str) -> date:
    """Try multiple date formats: YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY."""
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"):
        try:
            from datetime import datetime
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {s!r}")


def _parse_amount(s: str) -> Decimal:
    s = s.strip().replace(",", "").replace(" ", "")
    # Handle negative amounts (bank debits sometimes shown as negative)
    negative = s.startswith("-")
    s = s.lstrip("-").lstrip("+")
    try:
        val = Decimal(s)
        return abs(val)  # always store as positive; category determines income/expense
    except InvalidOperation:
        raise ValueError(f"Cannot parse amount: {s!r}")


def _parse_row(row: list[str], header_map: dict[str, int], row_num: int) -> ParsedRow:
    """Parse a single CSV data row using the header mapping. Raises ValueError on bad data."""
    def get(field: str) -> Optional[str]:
        idx = header_map.get(field)
        if idx is None or idx >= len(row):
            return None
        return row[idx].strip() or None

    date_str = get("transaction_date")
    if not date_str:
        raise ValueError("Missing transaction_date")
    tx_date = _parse_date(date_str)

    amount_str = get("amount_original")
    if not amount_str:
        raise ValueError("Missing amount_original")
    amount = _parse_amount(amount_str)
    if amount <= 0:
        raise ValueError("Amount must be positive")

    currency = (get("currency_original") or "JOD").upper()
    if currency not in VALID_CURRENCIES:
        currency = "JOD"

    category_raw = get("category")
    # Map to nearest valid category (case-insensitive), default to "Other"
    category = "Other"
    if category_raw:
        for valid in VALID_CATEGORIES:
            if valid.lower() == category_raw.lower():
                category = valid
                break

    description = get("description")

    return ParsedRow(
        transaction_date=tx_date,
        amount_original=amount,
        currency_original=currency,
        category=category,
        description=description,
    )


def import_csv(
    session: Session,
    user_id: UUID,
    file_content: bytes,
) -> ImportResult:
    """
    Parse and import a CSV file.
    - Good rows are imported immediately.
    - Bad rows are reported in errors but do not stop the import.
    - If the file cannot be parsed at all (bad encoding, no recognisable headers),
      raise ValueError (caller converts to HTTP 400).
    Returns ImportResult with counts.
    """
    from app.services.transactions import create_transaction

    try:
        text = file_content.decode("utf-8-sig")  # handle BOM
    except UnicodeDecodeError:
        text = file_content.decode("latin-1")

    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        raise ValueError("CSV file is empty")

    raw_headers = rows[0]
    header_map = _map_headers(raw_headers)

    required = {"transaction_date", "amount_original"}
    missing = required - set(header_map.keys())
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}. Download the template to see required headers.")

    imported = 0
    errors = []

    for row_num, row in enumerate(rows[1:], start=2):
        if not any(cell.strip() for cell in row):
            continue  # skip blank rows
        try:
            parsed = _parse_row(row, header_map, row_num)
            tx_data = TransactionCreate(
                amount_original=parsed.amount_original,
                currency_original=parsed.currency_original,
                category=parsed.category,
                description=parsed.description,
                transaction_date=parsed.transaction_date,
            )
            create_transaction(session, user_id, tx_data, source="csv_import")
            imported += 1
        except Exception as exc:
            errors.append({"row": row_num, "error": str(exc)})

    return ImportResult(imported=imported, errors=errors)
